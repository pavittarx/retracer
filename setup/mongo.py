from mongoy.mongo import Mongo

from dotenv import dotenv_values

config = dotenv_values('.env')

print('Config', config['MONGO_URI'])

mgo = Mongo(config['MONGO_URI'], config['DB'])

mgo.register_collection('signals')
mgo.register_collection('orders')
mgo.register_collection('trades')
mgo.register_collection('candles')