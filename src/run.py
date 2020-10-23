import sys
sys.path.append('/media/home/siminchen/repos/ad-tagging')
from flask import Flask, jsonify
import pandas as pd
import os
from flask import Flask, request
import time
from src.ad_tagger.tagger import RegexTagger

def init_tagger(config_path, attributes, l1):
    df_attrs_map = pd.read_excel(config_path)
    df_attrs_map = df_attrs_map.rename(columns = {'attr_name_nl-NL': 'attribute',
                                                'attr_value_nl-NL': 'value',
                                                'L1_name': 'l1',
                                                'L2_name': 'l2'
                                                })
    df_attrs_map = df_attrs_map[['l1', 'l2', 'attribute', 'value', 'attribute_type']].drop_duplicates()
    df_attrs_map = df_attrs_map[df_attrs_map['attribute'].isin(attributes) & (df_attrs_map['l1'] == l1)]
    tagger = RegexTagger.from_pandas(df_attrs_map)
    return tagger
    
tagger = init_tagger(config_path = 'data/single-multi-attributes.xlsx',
                     attributes = ['Kleur', 'Materiaal', 'Vorm', 'Lengte', 'Breedte', 'Hoogte'],
                     l1 = 'Huis en Inrichting')

app = Flask(__name__)

@app.route('/tag', methods=['GET'])
def api_tag():
    try:
        s = request.args['string']
        l2 = request.args['l2']
    except Exception:
        return jsonify({"error": "Parameters 'string' and 'l2' are required."})
    try:
        start = time.time()
        tags = tagger.tag(s, l2)
        elapse = time.time() - start
        message = {
            "tags": tags,
            "elapsed": elapse
        }
        return jsonify(message)
    except Exception as e:
        return jsonify({"error": "Tagger failure. string: {}, l2: {}. {}".format(s, l2, str(e))})


@app.route('/')
def home():
    return 'Regex tagger'

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

