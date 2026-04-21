/**
 * SCA — Google Apps Script Trigger
 *
 * Se ejecuta automáticamente cada vez que un candidato completa el
 * Google Form de postulación. Llama a la Claude Routine con:
 *   - URL del repositorio Git del candidato (GitHub, GitLab, Bitbucket)
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
const FIELD_EMAIL    = "Correo Electrónico (Email)";
const FIELD_REPO_URL = "Enlace al Repositorio (Link al Repositorio)"; // campo de tipo "Respuesta corta"

// Nombre de la carpeta raíz en Drive donde se guardarán los Excels de resultados
const RESULTS_FOLDER_NAME = "SCA - Resultados";

// Header de beta requerido por la API de Routines
const ROUTINES_BETA_HEADER = "experimental-cc-routine-2026-04-01";


// ─── Setup (correr una vez) ───────────────────────────────────────────────────

/**
 * Guarda los secrets en Script Properties.
 * Corré esta función manualmente desde el editor ANTES de activar el trigger.
 * Reemplazá los valores con los reales (ver routine/SETUP.md).
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

    const responses = e.namedValues;
    const nombre    = getCellValue(responses, FIELD_NOMBRE);
    const apellido  = getCellValue(responses, FIELD_APELLIDO);
    const email     = getCellValue(responses, FIELD_EMAIL);
    const repoUrl   = getCellValue(responses, FIELD_REPO_URL);

    if (!repoUrl) {
      Logger.log("❌ No se encontró URL del repositorio en la respuesta");
      return;
    }

    if (!isValidRepoUrl(repoUrl)) {
      Logger.log(`❌ URL inválida o no reconocida: ${repoUrl}`);
      notifyAdminOnError(new Error(`URL de repo inválida para ${apellido}, ${nombre}: ${repoUrl}`));
      return;
    }

    Logger.log(`Candidato: ${apellido}, ${nombre} (${email})`);
    Logger.log(`Repositorio: ${repoUrl}`);

    // Obtener o crear la carpeta de resultados en Drive
    const resultsFolderId = getOrCreateResultsFolder(apellido, nombre);
    Logger.log(`Carpeta de resultados: ${resultsFolderId}`);

    // Llamar a la Claude Routine
    const sessionId = callRoutineApi({
      repo_url:          repoUrl,
      results_folder_id: resultsFolderId,
      candidate: {
        nombre:   nombre,
        apellido: apellido,
        email:    email,
      },
    });

    Logger.log(`✅ Routine iniciada. Session ID: ${sessionId}`);

    // Guardar el Session ID en el Sheets para trazabilidad
    updateSheetWithSessionId(e, sessionId);

  } catch (error) {
    Logger.log(`❌ Error en onFormSubmit: ${error.message}\n${error.stack}`);
    notifyAdminOnError(error);
  }
}


// ─── Validación de URL ────────────────────────────────────────────────────────

/**
 * Verifica que la URL sea un repositorio Git reconocido.
 * Acepta GitHub, GitLab y Bitbucket (HTTP y SSH).
 */
function isValidRepoUrl(url) {
  const patterns = [
    /^https:\/\/github\.com\/.+\/.+/,
    /^https:\/\/gitlab\.com\/.+\/.+/,
    /^https:\/\/bitbucket\.org\/.+\/.+/,
    /^git@github\.com:.+\/.+\.git$/,
    /^git@gitlab\.com:.+\/.+\.git$/,
  ];
  return patterns.some(p => p.test(url.trim()));
}


// ─── Drive helpers ────────────────────────────────────────────────────────────

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
  const props        = PropertiesService.getScriptProperties();
  const endpointUrl  = props.getProperty("ROUTINE_ENDPOINT_URL");
  const routineToken = props.getProperty("ROUTINE_TOKEN");

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
    method:  "POST",
    headers: {
      "Authorization":     `Bearer ${routineToken}`,
      "anthropic-version": "2023-06-01",
      "anthropic-beta":    ROUTINES_BETA_HEADER,
      "Content-Type":      "application/json",
    },
    payload:            body,
    muteHttpExceptions: true,
  });

  const statusCode   = response.getResponseCode();
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
 * Agrega el Session ID de la Routine en la última columna de la fila enviada.
 * Útil para trazabilidad: sabés qué sesión corresponde a qué respuesta.
 */
function updateSheetWithSessionId(e, sessionId) {
  try {
    const sheet   = e.range.getSheet();
    const row     = e.range.getRow();
    const lastCol = sheet.getLastColumn();
    sheet.getRange(row, lastCol + 1).setValue(`Routine session: ${sessionId}`);
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
 * Reemplazá la URL del repo por una URL real de un repo de prueba.
 */
function testTrigger() {
  const mockEvent = {
    namedValues: {
      [FIELD_NOMBRE]:   ["Juan"],
      [FIELD_APELLIDO]: ["García"],
      [FIELD_EMAIL]:    ["juan@ejemplo.com"],
      [FIELD_REPO_URL]: ["https://github.com/juangarcia/prueba-tecnica"],
    },
    range: {
      getSheet: () => SpreadsheetApp.getActiveSpreadsheet().getActiveSheet(),
      getRow:   () => 2,
    },
  };

  onFormSubmit(mockEvent);
}
