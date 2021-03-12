import typing
from kolibri.model import Interpreter
from kolibri.features.features import Features
from kolibri.classifier.model import Classifier
from sklearn.pipeline import make_pipeline
from kolibri.document import Document
from lime.lime_text import LimeTextExplainer
import numpy as np
import os

class Explainer:
    def __init__(self, model: Interpreter=None):
        if model:
            self.model=model
            self.classifier=None
            self.begining_of_pipline=[]
            for component in self.model.pipeline:
                if isinstance(component, Classifier):
                    self.classifier=component.clf
                    self.class_names=component.class_names

    def load_model(self, path):
        model_interpreter = Interpreter.load(path)
        self.__init__(model_interpreter)

    def _predict(self, text):
        documents=[]
        for t in text:
            documents.append(Document(t))

        res=[]
        for d in documents:
            res.append(self.model.parse(d.text))

        predictions= [r['raw_prediction_results'][0] for r in res]

        if len(res)>0:
            self.class_names=res[0]['target']
#        print(np.asarray(predictions).shape)
        return np.asarray(predictions)

    def explain(self, text, id, save_path=None, nb_features=10, top_labels=2):


        explainer = LimeTextExplainer(class_names=self.class_names)



        exp = explainer.explain_instance(text, self._predict, num_features=nb_features, top_labels=top_labels)

        file_name=str(id)+"_lime_explanation.html"
        if save_path:
            file_name=os.path.join(save_path, file_name)

        exp.save_to_file(file_name)



if __name__=='__main__':
    model_directory = r"/Users/mohamedmentis/Documents/Mentis/Development/Python/Kolibri/examples/model/default/current"
    # model_interpreter = Interpreter.load(model_directory)

    explainer = Explainer()
    explainer.load_model(model_directory)
    text = "Bonjour,  Suite a votre mail du 22 mois, je voudrais vous faire savoir qu’il a un nouveau locataire au nom de Razvan Virgil Condruz en place depui le 1er mois..   EAN Gaz 541449020704582124  Indice au 01/09:  31479.291  Ean Electricite 541449020704582117 indice au 01/09 : 68546    Jean Mugabo +352671140784 "

    explainer.explain(text, 4, save_path='/Users/mohamedmentis/Documents/Mentis/Development/Python/Kolibri/examples')