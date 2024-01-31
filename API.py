import os
from flask import Flask, request, json, jsonify, abort
from waitress import serve
import logging
import json
import requests


##-------------------- Setting up logger ------------------##
logger = logging.getLogger('waitress')
logging.basicConfig(level=logging.INFO, format=f'%(asctime)s %(levelname)s: %(message)s')

##----------------------- Create App ----------------------##
app = Flask(__name__)

##----- Reading in and checking Environment Variables -----##

CS_AI_NO_AGREEMENT_ID = os.getenv("CS_AI_NO_AGREEMENT_ID")
if CS_AI_NO_AGREEMENT_ID == None:
    logging.error("CS_AI_NO_AGREEMENT_ID not in environment variables")
if not CS_AI_NO_AGREEMENT_ID.isdigit():
    logging.error("CS_AI_NO_AGREEMENT_ID must be an integer passed through as a string")

AI_UNCLASSIFIED_ID = os.getenv("AI_UNCLASSIFIED_ID")
if AI_UNCLASSIFIED_ID == None:
    logging.error("AI_UNCLASSIFIED_ID not in environment variables")
if not AI_UNCLASSIFIED_ID.isdigit():
    logging.error("AI_UNCLASSIFIED_ID must be an integer passed through as a string")

NOTHING_ID = os.getenv("NOTHING_ID")
if NOTHING_ID == None:
    logging.error("NOTHING_ID not in environment variables")
if not NOTHING_ID.isdigit():
    logging.error("NOTHING_ID must be an integer passed through as a string")

MAMMALWEB_ENDPOINT = os.getenv("MAMMALWEB_ENDPOINT")
if MAMMALWEB_ENDPOINT == None:
    logging.error("MAMMALWEB_ENDPOINT not in environment variables")

AUTH_DETAILS = os.getenv("AUTH_DETAILS")
if AUTH_DETAILS == None:
    logging.error("AUTH_DETAILS not in environment variables")

try:
    AUTH_DETAILS = json.loads(AUTH_DETAILS)
    required_auth_details = ["cognitoEndPoint", "clientId", "clientSecret"]
    for auth_detail in required_auth_details:
        if not auth_detail in AUTH_DETAILS:
            logging.error(f"{auth_detail} not in AUTH_DETAILS")

except Exception as e:
    logging.error("AUTH_DETAILS not formatted as a json string")


##------------------- Helper Functions -------------------##
def get_mw_api_token()-> None:
    try:
        logging.info("Getting MammalWeb API token.")
        data = {}
        headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        }
        
        cognito_response = requests.post(
            AUTH_DETAILS["cognitoEndPoint"], 
            headers=headers, 
            data=data, 
            auth=(AUTH_DETAILS["clientId"],AUTH_DETAILS["clientSecret"])
            )
        cognito_response.raise_for_status() 
        
        global MAMMALWEB_TOKEN
        MAMMALWEB_TOKEN = cognito_response.json()["access_token"]
        logging.info("Successfully obtained MammalWeb API token.")
    except KeyError as ke:
        logging.error(f"Unable to get MammalWeb token because of KeyError:\n    {ke} doesn't exist.")

    except Exception as e:
        logging.error(f"Unable to get MammalWeb token because:\n    {e}")


##-------------- Flask Routes and Functions -------------##
@app.errorhandler(400)
def incorrect_format(e):
    return jsonify(error=str(e)), 400

@app.errorhandler(500)
def incorrect_format(e):
    return jsonify(error=str(e)), 500

@app.route("/rule-of-thumb-v0", methods=["POST"])
def find_overlap_classification() -> None:
    allowed_content_type: list = ["application/json" , "text/plain"]
    content_type = request.headers.get('Content-Type')
    if content_type in allowed_content_type:
        try:
            data_in = json.loads(request.data)
            
            ai_type = data_in["ai_type"]
            ai_version = data_in["ai_version"]
            sequence_id = data_in["sequence_id"]
            human_species = data_in["human_species"]
            ai_species = data_in["ai_species"]

            ai_classifications = set(ai_species)
            if int(AI_UNCLASSIFIED_ID) in ai_classifications: #swap unclassified for nothing
                if AI_UNCLASSIFIED_ID == None:
                    abort(500, description="AI_UNCLASSIFIED_ID has not been set server side.")
                if NOTHING_ID == None:
                    abort(500, description="NOTHING_ID has not been set server side.")
                if not AI_UNCLASSIFIED_ID.isdigit():
                    logging.error("CS_AI_NO_AGREEMENT_ID must be an integer passed through as a string")
                if not NOTHING_ID.isdigit():
                    logging.error("NOTHING_ID must be an integer passed through as a string")
    
                ai_classifications.remove(int(AI_UNCLASSIFIED_ID))
                ai_classifications.add(int(NOTHING_ID))
            
            agreed_species = list(
                    set(human_species) & ai_classifications
                )
            
            if len(agreed_species)==0:
                if CS_AI_NO_AGREEMENT_ID == None:
                    abort(500, description="CS_AI_NO_AGREEMENT_ID has not been set server side.")
                if not CS_AI_NO_AGREEMENT_ID.isdigit():
                    logging.error("CS_AI_NO_AGREEMENT_ID must be an integer passed through as a string")
                agreed_species=[int(CS_AI_NO_AGREEMENT_ID)] 

            headers_out = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {MAMMALWEB_TOKEN}"
            }

            data_out =  json.dumps({
                "origin": "MammalWeb",
                "ai_type": ai_type,
                "ai_version": ai_version,
                "analysis_version": "Rule of Thumb v0",
                "sequence_id": sequence_id,
                "species":agreed_species 
                })
            
            try:
                response = requests.post(f"{MAMMALWEB_ENDPOINT}/analysis/ruleofthumb", headers=headers_out, data=data_out)
                if response.status_code == 403:
                    logging.info("Refreshing cognito token for MammalWeb API.")
                    get_mw_api_token()
                    headers_out = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {MAMMALWEB_TOKEN}"
                    }
                    response = requests.post(MAMMALWEB_ENDPOINT, headers=headers_out, data=data_out)
                response.raise_for_status() 
            except Exception as e:
                logger.error(e)
                logger.info(response.json())
                abort(500, description="Something went wrong on our side :( Please let us know and we will fix it.")
            
            return jsonify(data_out)

        except KeyError as ke:
            error_message = f"Data not formatted correctly. KeyError: {ke}"
            abort(400, description=error_message)
        except Exception as e:
            logger.error(e)
            abort(500, description="Something went wrong on our side :( Please let us know and we will fix it.")
    else:
        abort(400, description="Incompatable MIME type.")

    
if __name__ == "__main__":
    get_mw_api_token() # Gets valid api token for MammalWeb
    serve(app) # Serve Flask API with waitress