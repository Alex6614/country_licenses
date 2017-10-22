import requests
import json
import sys

# python github_get.py start sweden 5 
# python github_get.py continue sweden 5

# Check the numer of arguments
if(len(sys.argv) != 4):
	print("Wrong number of arguments\n Example: python github_get.py start|continue location no_of_iterations") 
	exit()

# Set up query and apply token
TOKEN = "19c67deb6357e7345bc899cfad3bddef184101c1"
LOCATION = sys.argv[2]
INCR_SIZE = "100"
ITERATIONS = int(sys.argv[3])

# If starting new query, create a new json, else read from licenses.json
licenses = {}
users = 0
if(sys.argv[1] == "start"):
	licenses = {
		"Eclipse Public License 1.0" : 0,
		"Mozilla Public License 2.0": 0,
		"BSD 2-clause \"Simplified\" License" : 0,
		"The Unlicense": 0,
		"MIT License": 0,
		"GNU General Public License v2.0": 0,
		"GNU Lesser General Public License v3.0": 0,
		"BSD 3-clause \"New\" or \"Revised\" License": 0,
		"Apache License 2.0": 0,
		"GNU General Public License v3.0": 0,
		"GNU Lesser General Public License v2.1": 0,
		"GNU Affero General Public License v3.0": 0,
		"Creative Commons Attribution 4.0": 0,
		"Other": 0,
		"none": 0
	}
elif(sys.argv[1] == "continue"):
	with open('licenses.json') as data_file:
		licenses = json.load(data_file)
	with open('users.txt') as data__file:
		users = int(data__file.readline())

else:
	print("Wrong first argument. Use continue or start")
	exit()

# Initialize some variables and the Header. init_cursor helps check if the cursor is not changing, indicating the end of users
cursor = ""
length_of_response = 0
header = {"Authorization": "token " + TOKEN}

# If start, create first query
if(sys.argv[1] == "start"):
	init_query = {'query' : 'query {search(first:' + INCR_SIZE + ', type: USER, query: "location:' + LOCATION + '") {edges { cursor node { ... on User { login location repositories(first: 20, isFork:false, orderBy: { field: STARGAZERS, direction: DESC}) {edges {node { name licenseInfo {name}}}}}}}}}'}
	post_data = json.dumps(init_query)

	# Post initial request
	post_response = requests.post(url='https://api.github.com/graphql', data=post_data, headers=header)

	# Find the number of nodes got
	length_of_response = len(post_response.json()["data"]["search"]["edges"])
	users = users + length_of_response
	# Traverse the JSON and add up details
	for user in post_response.json()["data"]["search"]["edges"]:
		# Some users do not have repositories
		if "repositories" not in user["node"]:
			continue
		for repo in user["node"]["repositories"]["edges"]:
			license = repo["node"]["licenseInfo"]
			if license is None:
				licenses["none"] = licenses["none"] + 1
			else:
				if license["name"] in licenses:
					licenses[license["name"]] = licenses[license["name"]] + 1
				else:
					licenses["Other"] = licenses["Other"] + 1

	# Get last cursor from last iteration
	cursor = post_response.json()["data"]["search"]["edges"][length_of_response - 1]["cursor"]

else:
	with open('cursor.txt') as data_file:
		cursor = data_file.readline()

# Start iterating
i = 0
while(i < ITERATIONS or length_of_response < int(INCR_SIZE)):
	# Make next request
	iter_query = {'query' : 'query {search(first:' + INCR_SIZE + ', type: USER, query: "location:' + LOCATION + '", after: "' + cursor + '") {edges { cursor node { ... on User { login location repositories(first: 20, isFork:false, orderBy: { field: STARGAZERS, direction: DESC}) {edges {node { name licenseInfo {name}}}}}}}}}'}
	iter_post_data = json.dumps(iter_query)
	post_iter_response = requests.post(url='https://api.github.com/graphql', data=iter_post_data, headers=header)
	
	# Find the number of nodes got
	length_of_response = len(post_iter_response.json()["data"]["search"]["edges"])
	users = users + length_of_response

	# Traverse JSON
	for user in post_iter_response.json()["data"]["search"]["edges"]:
		if "repositories" not in user["node"]:
			continue
		for repo in user["node"]["repositories"]["edges"]:
			license = repo["node"]["licenseInfo"]
			if license is None:
				licenses["none"] = licenses["none"] + 1
			else:
				if license["name"] in licenses:
					licenses[license["name"]] = licenses[license["name"]] + 1
				else:
					licenses["Other"] = licenses["Other"] + 1

	# Prepare for next iteration
	if length_of_response == 0:
		print("\n\n========== END OF USERS FOR " + LOCATION + " ==========\n\n")
		break
	cursor = post_iter_response.json()["data"]["search"]["edges"][length_of_response - 1]["cursor"]
	i = i + 1

f = open("licenses.json", "w+")
f.write(json.dumps(licenses))
f.close()
print(licenses)

g = open("cursor.txt", "w+")
g.write(cursor)
g.close()
print(cursor)

h = open("users.txt", "w+")
h.write(str(users))
h.close()
print(users)


# Since GitHub limits queries to 1000 results, I thought I'd just simply dump the licenses into a file
l = open(LOCATION + ".json", "w+")
l.write(json.dumps(licenses))
l.close()
