/**
 * SCA — Google Apps Script Trigger
 *
 * Se ejecuta automáticamente cada vez que un candidato completa el
 * Google Form de postulación. Llama a la Claude Routine con:
 *   - URL de descarga del ZIP desde Drive
 *   - Datos del candidato (nombre, apellido, email)
 *   - ID de la carpeta Drive donde guardar el Excel de resultados
 *
 * SETUP INICIAL (hacer una vez):
 *   1. Abrí el script en Apps Script Editor
 *   2. Corré la función setup() para configurar los secrets
 *   3. Agregá el trigger: Triggers → onFormSubmit → From spreadsheet → On form submit
 */


// ─── Constantes ───────────────────────────────────────────────────────────────

// Nombre de las columnas en el Google Form
// (ajustar si los nombres de las preguntas cambian)
const FIELD_NOMBRE   = "Nombre";
const FIELD_APELLIDO = "Apellido";
const FIELD_EMAIL    = "Email";
const FIELD_ZIP      = "ZIP de la solución"; // campo de tipo "Carga de archivos"

// Nombre de la carpeta en Drive donde se guardarán los Excels de resultados
const RESULTS_FOLDER_NAME = "SCA - Resultados";

// Header de beta requerido por la API de Routines
const ROUTINES_BETA_HEADER = "experimental-cc-routine-2026-04-01";


// ─── Setup (correr una vez) ───────────────────────────────────────────────────

/**
 * Guarda los secrets en Script Properties.
 * Corré esta función manualmente desde el editor ANTES de activar el trigger.
 * Reemplazá los valores con los reales.
 */
function setup() {
  const props = PropertiesService.getScriptProperties();
  props.setProperties({
    // URL del endpoint /fire de la Routine (la obtenés del web UI de Claude Code)
    // Formato: https://api.claude.ai/v1/routines/<routine_id>/fire
    ROUTINE_ENDPOINT_URL: "https://api.claude.ai/v1/routines/REPLACE_ME/fire",

    // Token bearer por-Routine (se genera en claude.ai/code/routines → Edit → API trigger)
    // Formato: sk-ant-oat01-xxxxx...
    ROUTINE_TOKEN: "sk-ant-oat01-REPLACE_ME",
  });
  Logger.log("✅ Secrets guardados en Script Properties.");
}


// ─── Trigger principal ────────────────────────────────────────────────────────

/**
 * Se ejecuta automáticamente al recibir una respuesta del formulario.
 * @param {Object} e - Evento de form submit
 */
function onFormSubmit(e) {
  try {
    Logger.log("Nueva respuesta recibida");

    const responses  = e.namedValues;
    const nombre     = getCellValue(responses, FIELD_NOMBRE);
    const apellido   = getCellValue(responses, FIELD_APELLIDO);
    const email      = getCellValue(responses, FIELD_EMAIL);
    const fileUrls   = responses[FIELD_ZIP];  // array de URLs de Drive

    if (!fileUrls || fileUrls.length === 0) {
      Logger.log("❌ No se encontró archivo ZIP en la respuesta");
      return;
    }

    Logger.log(`Candidato: ${apellido}, ${nombre} (${email})`);

    // Extraer el File ID desde la URL de Drive
    const driveUrl = fileUrls[0].trim();
    const fileId   = extractDriveFileId(driveUrl);

    if (!fileId) {
      Logger.log(`❌ No se pudo extraer el File ID de: ${driveUrl}`);
      return;
    }

    Logger.log(`File ID del ZIP: ${fileId}`);

    // Hacer el archivo accesible para descarga (anyone with link)
    const downloadUrl = makeFileDownloadable(fileId);
    Logger.log(`URL de descarga: ${downloadUrl}`);

    // Obtener o crear la carpeta de resultados en Drive
    const resultsFolderId = getOrCreateResultsFolder(apellido, nombre);
    Logger.log(`Carpeta de resultados: ${resultsFolderId}`);

    // Llamar a la Claude Routine
    const runId = callRoutineApi({
      zip_file_id:       fileId,
      zip_download_url:  downloadUrl,
      results_folder_id: resultsFolderId,
      candidate: {
        nombre:   nombre,
        apellido: apellido,
        email:    email,
      },
    });

    Logger.log(`✅ Routine iniciada. Session ID: ${runId}`);

    // Guardar el Session ID en el Sheets para trazabilidad
    updateSheetWithRunId(e, runId);

  } catch (error) {
    Logger.log(`❌ Error en onFormSubmit: ${error.message}\n${error.stack}`);
    // Notificar al admin por email si hay un error crítico
    notifyAdminOnError(error);
  }
}


// ─── Drive helpers ────────────────────────────────────────────────────────────

/**
 * Extrae el File ID de una URL de Google Drive.
 * Soporta los formatos:
 *   https://drive.google.com/open?id=FILE_ID
 *   https://drive.google.com/file/d/FILE_ID/view
 */
function extractDriveFileId(url) {
  // Formato: ?id=FILE_ID
  let match = url.match(/[?&]id=([a-zA-Z0-9_-]+)/);
  if (match) return match[1];

  // Formato: /file/d/FILE_ID/
  match = url.match(/\/file\/d\/([a-zA-Z0-9_-]+)/);
  if (match) return match[1];

  return null;
}

/**
 * Comparte el archivo con "anyone with the link" para que la Routine
 * pueda descargarlo sin autenticación.
 * Devuelve la URL de descarga directa.
 */
function makeFileDownloadable(fileId) {
  const file = DriveApp.getFileById(fileId);

  // Compartir con cualquier persona que tenga el link (solo lectura)
  file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);

  // URL de descarga directa (sin página de preview)
  return `https://drive.google.com/uc?export=download&id=${fileId}`;
}

/**
 * Obtiene o crea la carpeta de resultados para el candidato.
 * Estructura: "SCA - Resultados" / "Apellido_Nombre"
 */
function getOrCreateResultsFolder(apellido, nombre) {
  const rootFolders = DriveApp.getFoldersByName(RESULTS_FOLDER_NAME);
  let rootFolder;

  if (rootFolders.hasNext()) {
    rootFolder = rootFolders.next();
  } else {
    rootFolder = DriveApp.createFolder(RESULTS_FOLDER_NAME);
    Logger.log(`Carpeta raíz creada: ${RESULTS_FOLDER_NAME}`);
  }

  const candidateFolderName = `${apellido}_${nombre}`;
  const candidateFolders = rootFolder.getFoldersByName(candidateFolderName);
  let candidateFolder;

  if (candidateFolders.hasNext()) {
    candidateFolder = candidateFolders.next();
  } else {
    candidateFolder = rootFolder.createFolder(candidateFolderName);
    Logger.log(`Carpeta de candidato creada: ${candidateFolderName}`);
  }

  return candidateFolder.getId();
}


// ─── Claude Routines API ──────────────────────────────────────────────────────

/**
 * Dispara la Claude Routine vía el endpoint /fire y retorna el Session ID.
 *
 * Cada Routine tiene su propio endpoint URL y bearer token (se generan desde
 * claude.ai/code/routines → Edit → API trigger).
 *
 * El payload se serializa como JSON en el campo "text" (freeform string).
 * La Routine recibe ese string y lo parsea para extraer los datos del candidato.
 */
function callRoutineApi(payload) {
  const props           = PropertiesService.getScriptProperties();
  const endpointUrl     = props.getProperty("ROUTINE_ENDPOINT_URL");
  const routineToken    = props.getProperty("ROUTINE_TOKEN");

  if (!endpointUrl || endpointUrl.includes("REPLACE_ME")) {
    throw new Error("ROUTINE_ENDPOINT_URL no configurado. Corré setup() primero.");
  }
  if (!routineToken || routineToken.includes("REPLACE_ME")) {
    throw new Error("ROUTINE_TOKEN no configurado. Corré setup() primero.");
  }

  // El campo "text" es la única forma de pasar contexto a la Routine.
  // Lo enviamos como JSON serializado para que la Routine pueda parsearlo.
  const body = JSON.stringify({
    text: JSON.stringify(payload),
  });

  const response = UrlFetchApp.fetch(endpointUrl, {
    method:             "POST",
    headers: {
      "Authorization":  `Bearer ${routineToken}`,
      "anthropic-version": "2023-06-01",
      "anthropic-beta": ROUTINES_BETA_HEADER,
      "Content-Type":   "application/json",
    },
    payload:            body,
    muteHttpExceptions: true,
  });

  const statusCode  = response.getResponseCode();
  const responseBody = response.getContentText();

  if (statusCode !== 200 && statusCode !== 201) {
    throw new Error(`Routines API error ${statusCode}: ${responseBody}`);
  }

  const data = JSON.parse(responseBody);
  // La respuesta incluye session_id y session_url para ver el run en tiempo real
  Logger.log(`Session URL: ${data.session_url || "N/A"}`);
  return data.session_id || data.id || "unknown";
}


// ─── Sheets helpers ───────────────────────────────────────────────────────────

/**
 * Obtiene el valor de una pregunta del form por nombre.
 * namedValues es un objeto { "Pregunta": ["valor"] }
 */
function getCellValue(namedValues, fieldName) {
  const value = namedValues[fieldName];
  if (!value || value.length === 0) return "";
  return value[0].trim();
}

/**
 * Agrega el Run ID de la Routine en la última columna de la fila recién enviada.
 * Útil para trazabilidad: sabés qué run corresponde a qué respuesta.
 */
function updateSheetWithRunId(e, runId) {
  try {
    const sheet = e.range.getSheet();
    const row   = e.range.getRow();

    // Buscar la última columna con datos y escribir en la siguiente
    const lastCol = sheet.getLastColumn();
    sheet.getRange(row, lastCol + 1).setValue(`Routine session: ${runId}`);
  } catch (err) {
    Logger.log(`No se pudo actualizar el sheet: ${err.message}`);
  }
}


// ─── Error handling ───────────────────────────────────────────────────────────

/**
 * Envía un email al propietario del script si hay un error crítico.
 */
function notifyAdminOnError(error) {
  try {
    const email = Session.getActiveUser().getEmail();
    MailApp.sendEmail({
      to:      email,
      subject: "❌ SCA — Error en el trigger del formulario",
      body:    `Error: ${error.message}\n\nStack:\n${error.stack}`,
    });
  } catch (e) {
    Logger.log(`No se pudo enviar email de error: ${e.message}`);
  }
}


// ─── Test manual ─────────────────────────────────────────────────────────────

/**
 * Para probar sin necesidad de enviar el formulario.
 * Reemplazá FILE_ID con el ID real de un ZIP en Drive.
 */
function testTrigger() {
  const mockEvent = {
    namedValues: {
      [FIELD_NOMBRE]:   ["Juan"],
      [FIELD_APELLIDO]: ["García"],
      [FIELD_EMAIL]:    ["juan@ejemplo.com"],
      [FIELD_ZIP]:      ["https://drive.google.com/open?id=REPLACE_WITH_REAL_FILE_ID"],
    },
    range: {
      getSheet: () => SpreadsheetApp.getActiveSpreadsheet().getActiveSheet(),
      getRow:   () => 2,
    },
  };

  onFormSubmit(mockEvent);
}
