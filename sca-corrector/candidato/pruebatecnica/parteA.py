import os, json, sys, argparse

def main():
    path = get_args()
    solution = users_by_provider(path)
    with open(path+'users_by_provider.json', 'w') as fp:
        json.dump(solution, fp)

def get_args():
    parser = argparse.ArgumentParser(description='json file that indicates for each module which users requires it')
    parser.add_argument("--path", help="Path of users json files.", default='./')
    args = parser.parse_args()
    path = args.path
    return path

#Returns a dict with modules-providers-users for all json files in the specified path
def users_by_provider(path):
    module_provider_users = dict()
    json_file_names = [user_data for user_data in os.listdir(path) if user_data.endswith('.json')]
    for json_file_name in json_file_names:
        try:
            process_user_info(module_provider_users,path+json_file_name)    
        except:
            print('Something went wrong with file ' + json_file_name + ', please check it out.')
    return module_provider_users

#Adds user's info at json_path to dict module_provider_users
def process_user_info(module_provider_users, json_path):
    with open(json_path) as json_file:
        data = json.load(json_file)
        for module, provider in data['provider'].items():
            if not module in module_provider_users.keys():
                module_provider_users[module] = dict()
            if provider in module_provider_users[module].keys():
                module_provider_users[module][provider].append(json_path)
            else:
                module_provider_users[module][provider] = [json_path]     



if __name__ == "__main__":
    main()
