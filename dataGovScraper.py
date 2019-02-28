#!/usr/bin/env python3

import asyncio
from pyppeteer import launch
import sys

async def get_browser():
    return await launch({"headless": False})
    # return await launch()

async def get_page(browser, url):
    page = await browser.newPage()
    await page.goto(url)
    return page

async def search(page, topic): 
    searchURL = "https://catalog.data.gov/dataset?q={}&sort=score+desc%2C+name+asc&as_sfid=AAAAAAXAACc3aWbtYmov_VOD6pPUruoanETLfV-NRKbrYrOYqBSykdW8C96ePh4GJ5sH8quQjuFnBNBLu7T0zLc-kzmflM4bQ0vRf6D9agrAl5ZjizuKbfIBdP9yg0cQUNnUwtU%3D&as_fid=ea2f47a5682d1acb4124093d28bec0ce9275076e".format(topic)
    await page.goto(searchURL)
    await page.waitFor(2000)

async def readPage(page): 
    # this currently only gets 1 page 
    pageResults = await page.evaluate(
        '''() => {
        var searchResults = document.querySelectorAll('.dataset-content')
        var datasets = []
        var numExcessResources = 0
        for (item of searchResults) {
            organization = item.querySelector('.organization-type')
                                .querySelector('span')
                                .textContent

            datasetName = item.querySelector('.dataset-heading')
                                .querySelector('a')
                                .textContent

            dataFormats = [] 
            
            var resourceList = item.querySelector('.dataset-resources')
                                
            if (resourceList) {
                resourceList.querySelectorAll('li')
                            .forEach(df => dataFormats.push(df.querySelector('a').textContent))
            }

            if (dataFormats.length > 6) {
                numExcessResources = dataFormats[6].trim().split(" ")[0]
                dataFormats = dataFormats.slice(0,6)
            }

            datasets.push({organization, datasetName, dataFormats, numExcessResources})
        }
        return datasets
        }
        ''' 
    )
    return pageResults

async def getData(page, maxElem, topic):
    result = [] 
    nextPageAvail = True 

    searchURL = "https://catalog.data.gov/dataset?q={}&sort=score+desc%2C+name+asc&as_sfid=AAAAAAXAACc3aWbtYmov_VOD6pPUruoanETLfV-NRKbrYrOYqBSykdW8C96ePh4GJ5sH8quQjuFnBNBLu7T0zLc-kzmflM4bQ0vRf6D9agrAl5ZjizuKbfIBdP9yg0cQUNnUwtU%3D&as_fid=ea2f47a5682d1acb4124093d28bec0ce9275076e".format(topic)

    TOTAL_RESULTS = "#content > div.row.wrapper > div > section:nth-child(1) > div.new-results"
    header = await page.evaluate(
        ''' (sel) => 
        document.querySelector(sel).textContent
        ''', TOTAL_RESULTS
    )

    numResults = int(header.split()[0])
    pgNum = 1

    if maxElem == None: 
        maxElem = numResults + 1

    while len(result) < maxElem and nextPageAvail: 
        
        result.extend(await readPage(page))

        # next page: 
        pgNum += 1
        nextPageURL = searchURL + "&page=" + str(pgNum)
        await page.goto(nextPageURL)

        # check nextPageAvail Bool
        nextPageAvail = (len(result) < numResults)

    print(result[:maxElem])
    return result[:maxElem] 

async def run(url, topic, maxElem):
    # open data.gov 
    browser = await get_browser()
    page = await get_page(browser, url) 
    # search string 
    await search(page, topic)
    await page.waitFor(2000)
    # pull n number of results or max available  
    await getData(page, maxElem, topic)


if __name__ == '__main__':  
    url = "https://www.data.gov/"
    loop = asyncio.get_event_loop()
    topic = sys.argv[1]
    maxElem = int(sys.argv[2])

    if maxElem <= 0: 
        print('Max Elements must be greater than 1!')
         
    else:  
        result = loop.run_until_complete(run(url, topic, maxElem))