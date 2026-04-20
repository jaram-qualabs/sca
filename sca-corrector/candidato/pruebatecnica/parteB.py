import os, json, sys, argparse

def main():
    path = get_args()
    users_providers = users_provider_dict(path)
    print(minimum_users_required(users_providers))

def get_args():
    parser = argparse.ArgumentParser(description='json file that indicates for each module which users requires it')
    parser.add_argument("--path", help="Path of users json files.", default='./')
    args = parser.parse_args()
    path = args.path
    return path

#Returns a dict of providers used by user
def users_provider_dict(path):
    user_providers = dict()
    json_file_names = [user_data for user_data in os.listdir(path) if user_data.endswith('.json')]
    for json_file_name in json_file_names:
        try:
            process_user_info(user_providers,path+json_file_name)    
        except:
            print('Something went wrong with file ' + json_file_name + ', please check it out.')
    return user_providers

#Adds the user's providers of json_path to user_providers
def process_user_info(user_providers,  json_path):
    with open(json_path) as json_file:
        data = json.load(json_file)
        for _, provider in data['provider'].items():
            if not json_path in user_providers.keys():
                user_providers[json_path] = set()
            user_providers[json_path].add(provider)    

#Greedy solution for minimal hitting problem
def minimum_users_required(user_providers):
    universe = get_universe(user_providers)
    selected_users = []

    while len(universe) != 0: # As long as there are unused providers
        user_largest_subset, largest_subset = get_largest_subset(user_providers, universe)
        selected_users.append(user_largest_subset)
        universe = universe - largest_subset #Remove providers visited by the user with the largest amount of required providers

    return selected_users

#Returns a set with every provider of user_providers
def get_universe(user_providers):
    universe = set()
    for _,providers in user_providers.items():
        universe.update(providers)
    return universe

#Returns the user with the largest set of providers that haven't been already used, and that set
def get_largest_subset(user_providers, universe):
    max_length = 0
    user_largest_subset = None
    largest_subset = set()
    
    for user, providers in user_providers.items():
        intersection = providers.intersection(universe) # Only consider providers not alreay used by other users
        if len(intersection) > max_length:
            max_length = len(intersection)
            user_largest_subset = user
            largest_subset = intersection

    user_providers.pop(user,None)

    return user_largest_subset, largest_subset

if __name__ == "__main__":
    main()
