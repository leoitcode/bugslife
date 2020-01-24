from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
import uvicorn, aiohttp, asyncio
import os
from io import BytesIO

from fastai import *
from fastai.vision import *

export_file_url = 'https://drive.google.com/uc?export=download&id=1w5iRzJyYal2v8VZojwjHubJY7hT9MRTk'

export_file_name = 'export.pkl'

classes = ['accessory',
'animal',
'ant',
'appliance',
'assassin',
'bed-bug',
'bee',
'beetle',
'butterfly',
'catterpillar',
'cicadomorpha-bug',
'cockroach',
'crickets',
'dragonfly',
'electronic',
'flies',
'food',
'furniture',
'indoor',
'kitchen',
'lacewing',
'leaf-footed-squash-bug',
'outdoor',
'person',
'plant-bug',
'planthopper-bug',
'seed-bug',
'sports',
'stink-shield-bug',
'termites',
'thrips',
'vehicle',
'wasp']

path = Path(__file__).parent

app = Starlette()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_headers=['X-Requested-With', 'Content-Type'])
app.mount('/static', StaticFiles(directory='app/static'))

async def download_file(url, dest):
    if dest.exists(): return
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.read()
            with open(dest, 'wb') as f: f.write(data)

async def setup_learner():
    await download_file(export_file_url, path/export_file_name)
    try:
        learn = load_learner(path, export_file_name)
        return learn
    except RuntimeError as e:
        if len(e.args) > 0 and 'CPU-only machine' in e.args[0]:
            print(e)
            message = "\n\nThis model was trained with an old version of fastai and will not work in a CPU environment.\n\nPlease update the fastai library in your training environment and export your model again.\n\nSee instructions for 'Returning to work' at https://course.fast.ai."
            raise RuntimeError(message)
        else:
            raise

loop = asyncio.get_event_loop()
tasks = [asyncio.ensure_future(setup_learner())]
learn = loop.run_until_complete(asyncio.gather(*tasks))[0]
loop.close()

@app.route('/')
def index(request):
    html = path/'view'/'index.html'
    return HTMLResponse(html.open().read())

@app.route('/analyze', methods=['POST'])
async def analyze(request):
    data = await request.form()
    img_bytes = await (data['file'].read())
    img = open_image(BytesIO(img_bytes))
    prediction = learn.predict(img)[0]
    all_insect = ['ant','assassin','bed-bug','bee','beetle','butterfly','catterpillar',\
    'cicadomorpha-bug','cockroach','crickets','dragonfly','flies','lacewing',\
    'leaf-footed-squash-bug','plant-bug','planthopper-bug','seed-bug',\
    'stink-shield-bug']

    if str(prediction) in all_insect:
        return JSONResponse({'result':'É um inseto'})
    else:
        return JSONResponse({'result':'Não é inseto'})
        
@app.route('/bug_analyze', methods=['POST'])
async def bug_analyze(request):
    form = await request.form()
    img = await form["file"].read()
    img = open_image(BytesIO(img))
    prediction = learn.predict(img)[0]
    all_insect = ['ant','assassin','bed-bug','bee','beetle','butterfly','catterpillar',\
    'cicadomorpha-bug','cockroach','crickets','dragonfly','flies','lacewing',\
    'leaf-footed-squash-bug','plant-bug','planthopper-bug','seed-bug',\
    'stink-shield-bug']

    if str(prediction) in all_insect:
        return JSONResponse({'result':1})
    else:
        return JSONResponse({'result':0})


if __name__ == '__main__':
    if 'serve' in sys.argv:
        port = int(os.getenv('PORT', 5042))
        uvicorn.run(app=app, host='0.0.0.0', port=port)
