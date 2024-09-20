import json
import spacy
import requests
import logging


from nltk import Tree
from time import time 

from presidio_analyzer import AnalyzerEngine
from openai import AzureOpenAI

api_version = "2023-07-01-preview"
endpoint = "https://model-serving.us-east-2.int.infra.intelligence.webex.com/azure/v1"

client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key="MzQyYTU0ODktZjgwMy00MDEyLTk0ZDAtZjE0MmJjZTk1MzQ2YmVjOTkyOWEtMWRh_A52D_1eb65fdf-9643-417f-9974-ad72cae0e10f"
)


pos_dict = {
    'ADJ': 'adjective',
    'ADP': 'adposition',
    'ADV': 'adverb',
    'AUX': 'auxiliary verb',
    'CONJ': 'conjunction',
    'CCONJ': 'coordinating conjunction',
    'DET': 'determiner',
    'INTJ': 'interjection',
    'NOUN': 'noun',
    'NUM': 'numeral',
    'PART': 'particle',
    'PRON': 'pronoun',
    'PROPN': 'proper noun',
    'PUNCT': 'punctuation',
    'SCONJ': 'subordinating conjunction',
    'SYM': 'symbol',
    'VERB': 'verb',
    'X': 'other',
    'SPACE': 'space',
}


CONV_DISCUSSING_PII = "is_discussing_pii"
CONV_DISCUSSING_PII_ENTITY = "discussing_pii_entity"

INTENT_CLASSIFICATION = "intent_classification"
PII_INFO_FOUND = "pii_info_found"

FINAL_VERDICT = "has_pii"
MAYBE_VERDICT = "maybe_has_pii"


class SpacyToken:
    def __init__(self, token) -> None:
        self.token = token
    
    def get_children(self):
        return [SpacyToken(x).to_dict() for x in self.token.children]
    
    def to_dict(self):
        return {
            "text": self.token.text,
            "lemma": self.token.lemma_,
            "pos": self.token.pos_,
            "pos_exp": pos_dict.get(self.token.pos_),
            "dep": self.token.dep_,
            "children": self.get_children(),
        }

logger = logging.getLogger(__name__)
analyzer = AnalyzerEngine()
nlp = spacy.load("en_core_web_trf")


def timer_func(func): 
    # This function shows the execution time of  
    # the function object passed 
    def wrap_func(*args, **kwargs): 
        t1 = time() 
        result = func(*args, **kwargs) 
        t2 = time() 
        # logger.warn(f'Function {func.__name__!r} executed in {(t2-t1):.4f}s') 
        return result 
    return wrap_func


class TextPIIParser:
    @timer_func
    def __init__(self) -> None:
        self.text = None
        self.entities = ["PHONE_NUMBER", "CREDIT_CARD", "CRYPTO", "DATE_TIME", "IBAN_CODE", "NRP", "LOCATION",  "MEDICAL_LICENSE", "URL", "US_BANK_NUMBER", "US_DRIVER_LICENSE", "US_ITIN", "US_PASSPORT", "US_SSN"]

        self.final_result = dict()
    
    def process_new_input(self, text):
        self.text = text
        self.final_result = {
            CONV_DISCUSSING_PII: False,
            INTENT_CLASSIFICATION: None,
            PII_INFO_FOUND: [],
            FINAL_VERDICT: False,
            MAYBE_VERDICT: False,
        }
    
    @timer_func
    def presidio_analyze(self):
        results = analyzer.analyze(text=self.text, entities=self.entities, language='en')
        results = [x.to_dict() for x in results]
        for result in results:
            result["raw"] = self.text[result["start"]:result["end"]]

        piis = []
        for result in results:
            pii = result["raw"]
            if pii not in piis:
                piis.append(pii)
        
        self.final_result[PII_INFO_FOUND] = piis
    
    @timer_func
    def nltk_analyze(self):
        doc = nlp(self.text)
        nouns = [(token, token.pos_) for token in doc if token.pos_ in ["NOUN", "PROPN"]]
        logger.warn(f"Nouns: {nouns}")

        sub_toks = [tok for tok in doc if (tok.dep_ == "nsubj") ]
        logger.warn(f"Subj: {sub_toks}")

        # Find named entities, phrases and concepts
        for entity in doc.ents:
            logger.warn(f"{entity.text=}")
            logger.warn(f"{entity.label_=}")

        pos_dict = {
            'ADJ': 'adjective',
            'ADP': 'adposition',
            'ADV': 'adverb',
            'AUX': 'auxiliary verb',
            'CONJ': 'conjunction',
            'CCONJ': 'coordinating conjunction',
            'DET': 'determiner',
            'INTJ': 'interjection',
            'NOUN': 'noun',
            'NUM': 'numeral',
            'PART': 'particle',
            'PRON': 'pronoun',
            'PROPN': 'proper noun',
            'PUNCT': 'punctuation',
            'SCONJ': 'subordinating conjunction',
            'SYM': 'symbol',
            'VERB': 'verb',
            'X': 'other',
            'SPACE': 'space',
        }

        for token in doc:
            logger.warn(json.dumps(indent=4, obj={
                "text": token.text, 
                "lemma": token.lemma_, 
                "pos": token.pos_, 
                "pos_exp": pos_dict.get(token.pos_), 
                "test": str(token.head),
                "c": [str(x) for x in token.children],
                "dep": token.dep_, 
            }))
        
        logger.warn("###")

        objects = [SpacyToken(tok) for tok in doc if ("obj" in tok.dep_) ]
        logger.warn(f"Objects: {json.dumps(indent=4, obj=[x.to_dict() for x in objects])}")
    
    @timer_func
    def analyze_openai(self):
        question = f"""
            "{self.text}" Is PII asked for in this? Answer in yes/no
        """.strip()
        completion = client.chat.completions.create(
            model="gpt-35-turbo",
            messages=[
                {
                    "role": "user",
                    "content": question,
                },
            ],
        )
        logger.warn(completion.model_dump_json(indent=4))
        
        self.final_result[CONV_DISCUSSING_PII] = "yes" in json.loads(completion.model_dump_json(indent=4))["choices"][0]["message"]["content"].lower()

        self.analyze_openai_pii()
    
    def analyze_openai_pii(self):
        question = f"""
            "{self.text}" does this have any PII? If so then answer in one word and mention the PII in double quotes
        """.strip()
        completion = client.chat.completions.create(
            model="gpt-35-turbo",
            messages=[
                {
                    "role": "user",
                    "content": question,
                },
            ],
        )
        logger.warn(completion.model_dump_json(indent=4))
        pii_entity = None
        result = json.loads(completion.model_dump_json(indent=4))["choices"][0]["message"]["content"].lower()
        if '"' in result:
            # pii_entity is the text between two quotes
            pii_entity = result.split('"')[1]
        
        self.final_result[CONV_DISCUSSING_PII_ENTITY] = pii_entity

        # if openai is only saying "pii" then we will mark it as false positive
        false_positive_list = ["pii", "yes", "no", "color", "colour", "name"]
        if pii_entity and pii_entity.lower in false_positive_list:
            self.final_result[CONV_DISCUSSING_PII_ENTITY] = None
            self.final_result[CONV_DISCUSSING_PII] = False

    @timer_func
    def rasa_analyze(self):
        url = "http://10.53.60.89:5005/model/parse"
        payload = json.dumps({
            "text": self.text,
        })
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        response_dict = json.loads(response.text)
        entities = response_dict.get("entities", None)

        if "intent" in response_dict and "confidence" in response_dict["intent"]:
            if response_dict["intent"]["confidence"] < 0.9:
                return

        if entities:
            match_flag = False
            for entity in entities:
                if len(entity["entity"].split("_")) > len(entity["value"].split(" ")):
                    continue
                match_flag = True
            
            if match_flag:
                # self.final_result[INTENT_CLASSIFICATION] = (response_dict["intent"]["name"], f"{int(response_dict['intent']['confidence'] * 100)}%")
                self.final_result[INTENT_CLASSIFICATION] = response_dict["intent"]["name"]
                # logger.warn(json.dumps(indent=4, obj=response_dict))

    # def process_piis(self):
    #     for result in self.presidio_result:
    #         pii = result["raw"]
    #         if pii not in self.pii_dict:
    #             self.pii_dict[pii] = []
    #         self.pii_dict[pii].append(result["entity_type"])
    
    # def get_piis(self):
    #     piis = []
    #     for result in self.presidio_result:
    #         pii = result["raw"]
    #         if pii not in piis:
    #             piis.append(pii)
    #     return piis

    # @timer_func
    # def pretty_print(self):
    #     print(json.dumps(indent=4, obj=self.presidio_result))
    #     print(f"{self.get_piis()=}")

    #     print(f"### {json.dumps(indent=4, obj=self.pii_dict)}")
    
    @timer_func
    def process(self, text):
        self.process_new_input(text)
        self.presidio_analyze()
        self.nltk_analyze()

        try:
            self.rasa_analyze()
        except Exception as e:
            logger.error(f"Rasa error: {e}")
        
        try:
            self.analyze_openai()
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
        
        self.final_result[FINAL_VERDICT] = False
        self.final_result[MAYBE_VERDICT] = False

        # OpenAI has detected PII
        if self.final_result[CONV_DISCUSSING_PII]:
            self.final_result[FINAL_VERDICT] = True
        
        # Rasa has found PII but OpenAI has not
        if self.final_result[INTENT_CLASSIFICATION]:
            if not self.final_result[CONV_DISCUSSING_PII]:
                self.final_result[MAYBE_VERDICT] = True
        
        # Microsoft Presidio has found PII but OpenAI has not

        # if final verdict is true the set maybe as true
        if self.final_result[FINAL_VERDICT]:
            self.final_result[MAYBE_VERDICT] = True

@timer_func
def process_text(text):
    text_parser = TextPIIParser()
    text_parser.process(text)
    return text_parser.final_result


def main():
    text_parser = TextPIIParser()
    text = "I hold a MasterCard with number 4111 1111 1111 1111, expiring on 12/23, with CVV 456. My medical license number is X1234567. My SSN is 123-45-6789. My health insurance ID is ABC123456789. My ITIN is 123456789. My passport number is 123456789. My driver's license number is 123456789. My bank account number is 123456789."
    text_parser.process(text)
    

if __name__ == "__main__":
    main()
