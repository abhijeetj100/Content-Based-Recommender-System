from fastapi import FastAPI, Form, Request
from fastapi.templating import Jinja2Templates
import uvicorn
import math
import pandas as pd

# Newsapi-python uses news api at newsapi.org to fetch news articles from various domains and sources
# https://newsapi.org/
from newsapi import NewsApiClient

# Setting up FastApi
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Initializing newsapi client connection
api = NewsApiClient(api_key='d8eda0752a604d0dba99f82ffbe1fcc9')

# Utility function for computing TF Score
def computeTFScore(wordDict, bow):
    tfDict = {}
    bowCount = len(bow)
    for word, count in wordDict.items():
        tfDict[word] = count/float(bowCount)
    return tfDict

# Utility function for computing IDF Score
def computeIDFScore(docList):

    # idfDict = {}
    N = len(docList)

    idf_dict = dict.fromkeys(docList[0].keys(), 0)
    for doc in docList:
        for word, val in doc.items():
            if val > 0:
                idf_dict[word] += 1

    for word, val in idf_dict.items():
        idf_dict[word] = math.log10(N / float(val))
    return idf_dict

# Utility function for computing TFIDF Score
def computeTFIDFScore(tfBow, idfs):
    tfidf = {}
    for word, val in tfBow.items():
        tfidf[word] = val*idfs[word]
    return tfidf

# Utility function for search_query
def search_query(academic_info: str, job_info: str, skill_set: str):
    bowA=academic_info.split(" ")
    bowB=job_info.split(" ")
    bowC=skill_set.split(" ")
    wordset=set(bowA).union(set(bowB)).union(set(bowC))
    # wordset=wordset.union(set(bowC))

    wordDictA = dict.fromkeys(wordset, 0)
    wordDictB = dict.fromkeys(wordset, 0)
    wordDictC = dict.fromkeys(wordset, 0)

    for word in bowA:
        wordDictA[word] += 1

    for word in bowB:
        wordDictB[word] += 1

    for word in bowC:
        wordDictC[word] += 1

    tfBowA = computeTFScore(wordDictA, bowA)
    tfBowB = computeTFScore(wordDictB, bowB)
    tfBowC = computeTFScore(wordDictC, bowC)

    idfs = computeIDFScore([wordDictA, wordDictB, wordDictC])

    tfidfBowA = computeTFIDFScore(tfBowA, idfs)
    tfidfBowB = computeTFIDFScore(tfBowB, idfs)
    tfidfBowC = computeTFIDFScore(tfBowC, idfs)

    df=pd.DataFrame([tfidfBowA, tfidfBowB, tfidfBowC])
    print(df)
    query = ""

    for word in wordset:
        maxClm = df[word].max()
        if (maxClm >= 0.1):
            query = query+" "+ word
    return query

# Http GET endpoint for the index page asking for user input
@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", context={"request": request})

# Http POST endpoint for returning the content-based filtered recommendations
@app.post("/recommend")
async def submit(request: Request, academic_info: str = Form(...), job_info: str = Form(...), skill_set: str = Form(...)):
    user_profile = "\nAcademic Information: "+academic_info+";\nJob Information: "+job_info+";\nSkill Set: "+skill_set+";"
    query_string = search_query(academic_info, job_info, skill_set)
    results = api.get_everything(q=query_string)
    total_news=""
    count=0
    for result in results['articles']:
        count=count+1
        total_news = total_news + "\n\n"+str(count)+".)\nTITLE: " + result['title'] + "\nDESC: " + result['description'] + "\nURL: " + result['url']+"\n"
    return templates.TemplateResponse("recommendations.html", context={"request": request, "profile": user_profile, "news": total_news})

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)

