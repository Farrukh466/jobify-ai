import http.client

conn = http.client.HTTPSConnection("linkedin-job-search-api.p.rapidapi.com")

headers = {
    'x-rapidapi-key': "3928ef76dbmsh3fdca79a275933dp15f5c5jsn5c4c2152e54b",
    'x-rapidapi-host': "linkedin-job-search-api.p.rapidapi.com"
}

conn.request("GET", "/active-jb-1h?offset=0&title_filter=%22Data%20Engineer%22&location_filter=%22United%20States%22%20OR%20%22United%20Kingdom%22", headers=headers)

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))