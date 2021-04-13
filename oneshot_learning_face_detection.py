# -*- coding: utf-8 -*-
"""oneshot learning face detection.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1zieCzy4tN_jeH1NUPwkldI0MbWn1_JSF
"""

# Instalations
!pip install mtcnn

# Imports
from os import listdir
from PIL import Image
from numpy import asarray
from numpy import savez_compressed
from numpy import load
from matplotlib import pyplot
from mtcnn.mtcnn import MTCNN
from os.path import isdir
from numpy import expand_dims
from keras.models import load_model

from google.colab import drive
drive.mount('/content/drive')

# extrair uma única face de um arquivo
def extract_face(filename, required_size=(160, 160)):
	image = Image.open(filename)
	# convert to RGB, remove transparências
	image = image.convert('RGB')
	pixels = asarray(image)
	detector = MTCNN()
	# detectar a face
	results = detector.detect_faces(pixels)
	x1, y1, width, height = results[0]['box']
	# bug fix (remove valores negativos)
	x1, y1 = abs(x1), abs(y1)
	x2, y2 = x1 + width, y1 + height
	# seleciona a face
	face = pixels[y1:y2, x1:x2]
	# redefine o tamanho para o padrão
	image = Image.fromarray(face)
	image = image.resize(required_size)
	face_array = asarray(image)
	return face_array

# extrair diversas faces de uma fotografia
def extract_faces(filename, required_size=(160, 160)):
	image = Image.open(filename)
	image = image.convert('RGB')
	pixels = asarray(image)
	detector = MTCNN()
	results = detector.detect_faces(pixels)
	faces = list()
	for result in results: 
		x1, y1, width, height = result['box']
		x1, y1 = abs(x1), abs(y1)
		x2, y2 = x1 + width, y1 + height
		face = pixels[y1:y2, x1:x2]
		image = Image.fromarray(face)
		image = image.resize(required_size)
		face_array = asarray(image)
		faces.append(face_array)
	return asarray(faces)

# pegar todas as faces de uma pasta
def load_faces(directory):
	faces = list()
	for filename in listdir(directory):
		path = directory + filename
		face = extract_face(path)
		faces.append(face)
	return faces

# carregar database que contem várias pastas e imagens nessas pastas
def load_dataset(directory):
	X, y = list(), list()
	for subdir in listdir(directory):
		path = directory + subdir + '/'
		if not isdir(path):
			continue
		faces = load_faces(path)
		labels = [subdir for _ in range(len(faces))]
		print('>loaded %d examples for class: %s' % (len(faces), subdir))
		X.extend(faces)
		y.extend(labels)
	return asarray(X), asarray(y)

# carregar treino
trainX, trainy = load_dataset('/content/drive/MyDrive/PDI2/train/')
print(trainX.shape, trainy.shape)
# carregar teste
testX, testy = load_dataset('/content/drive/MyDrive/PDI/test/')
print(testX.shape, testy.shape)
# salvar comprimido
savez_compressed('classification-dataset.npz', trainX, trainy, testX, testy)

# calculo de embedding
def get_embedding(model, face_pixels):
	face_pixels = face_pixels.astype('float32')
	mean, std = face_pixels.mean(), face_pixels.std()
	face_pixels = (face_pixels - mean) / std
	samples = expand_dims(face_pixels, axis=0)
	yhat = model.predict(samples)
	return yhat[0]

# carregar o dataset
data = load('classification-dataset.npz', allow_pickle=True)
trainX, trainy, testX, testy = data['arr_0'], data['arr_1'], data['arr_2'], data['arr_3']
print('Loaded: ', trainX.shape, trainy.shape, testX.shape, testy.shape)
# carrega o modelo
model = load_model('/content/drive/MyDrive/PDI/facenet_keras.h5')
print('Loaded Model')
# converte as imagens de treino em embeddings
newTrainX = list()
for face_pixels in trainX:
	embedding = get_embedding(model, face_pixels)
	newTrainX.append(embedding)
newTrainX = asarray(newTrainX)
print(newTrainX.shape)
# convert as imagens de teste em embedding
newTestX = list()
for face_pixels in testX:
	embedding = get_embedding(model, face_pixels)
	newTestX.append(embedding)
newTestX = asarray(newTestX)
print(newTestX.shape)
# save arrays to one file in compressed format
savez_compressed('classification-embeddings.npz', newTrainX, trainy, newTestX, testy)

# aplicando tudo
from numpy import load
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import Normalizer
from sklearn.svm import SVC
# carregar embeddings
data = load('classification-embeddings.npz')
trainX, trainy, testX, testy = data['arr_0'], data['arr_1'], data['arr_2'], data['arr_3']
print('Dataset: train=%d, test=%d' % (trainX.shape[0], testX.shape[0]))

in_encoder = Normalizer(norm='l2')
trainX = in_encoder.transform(trainX)
testX = in_encoder.transform(testX)

out_encoder = LabelEncoder()
out_encoder.fit(trainy)
trainy = out_encoder.transform(trainy)
testy = out_encoder.transform(testy)
# treinar modelo
model = SVC(kernel='linear', probability=True)
model.fit(trainX, trainy)
# predizer
yhat_train = model.predict(trainX)
yhat_test = model.predict(testX)
# calculos
score_train = accuracy_score(trainy, yhat_train)
score_test = accuracy_score(testy, yhat_test)

print('Accuracy: train=%.3f, test=%.3f' % (score_train*100, score_test*100))

# teste com foto de sala de aula
from random import choice
from numpy import load
from numpy import expand_dims
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import Normalizer
from sklearn.svm import SVC
from matplotlib import pyplot
# carrega as faces
data = load('classification-dataset.npz')
testX_faces = data['arr_2']
# carrega os embeddings
data = load('classification-embeddings.npz')
trainX, trainy, testX, testy = data['arr_0'], data['arr_1'], data['arr_2'], data['arr_3']

in_encoder = Normalizer(norm='l2')
trainX = in_encoder.transform(trainX)
testX = in_encoder.transform(testX)

out_encoder = LabelEncoder()
out_encoder.fit(trainy)
trainy = out_encoder.transform(trainy)
testy = out_encoder.transform(testy)
# treino
model = SVC(kernel='linear', probability=True)
model.fit(trainX, trainy)

# definição de resultado esperado
class_faces = extract_faces('/content/drive/MyDrive/PDI/classroom/class1.jpg')
class1ExpectedResult = {
    "ant_man": True,
    "capitao_america": True,
    "drax": True,
    "falcao": True,
    "gamora": True,
    "gaviao_arqueiro": True,
    "homem_aranha": True,
    "hulk": True,
    "ironman": True,
    "pantera_negra": True,
    "star_lord": True,
    "strange": True,
    "thor": True,
    "viuva_negra": True,
    "wanda": True,
    "war_machine": True
}
# prep para onde serão salvos os resultados encontrados
class1Results = {
    "ant_man": False,
    "capitao_america": False,
    "drax": False,
    "falcao": False,
    "gamora": False,
    "gaviao_arqueiro": False,
    "homem_aranha": False,
    "hulk": False,
    "ironman": False,
    "pantera_negra": False,
    "star_lord": False,
    "strange": False,
    "thor": False,
    "viuva_negra": False,
    "wanda": False,
    "war_machine": False
}
classroom = list()

model2 = load_model('/content/drive/MyDrive/PDI/facenet_keras.h5')
for face_pixels in class_faces:
	print(face_pixels.shape)
	embedding = get_embedding(model2, face_pixels)
	classroom.append(embedding)
 
classroom = asarray(classroom)
in_encoder = Normalizer(norm='l2')
faces = in_encoder.transform(classroom)
cont = 0
for face in faces:
  samples = expand_dims(face, axis=0)
  yhat_class = model.predict(samples)
  yhat_prob = model.predict_proba(samples)
  class_index = yhat_class[0]
  class_probability = yhat_prob[0,class_index] * 100
  predict_names = out_encoder.inverse_transform(yhat_class)
  title = '%s (%.3f)' % (predict_names[0], class_probability)
  class1Results[predict_names[0]] = True
  cont += 1
print (class1ExpectedResult)
print (class1Results)
total = len(class1ExpectedResult)
corrects = 0
false_positives = 0
false_negatives = 0
for key in class1ExpectedResult:
  if class1Results[key] == class1ExpectedResult[key]: 
    corrects += 1
  elif class1Results[key] == True:
      false_positives += 1
  else: 
      false_negatives += 1 

print("Acertou %.3f" % (corrects/total * 100))
print("Falsos positivos %.3f" % (false_positives/total * 100))
print("Falsos negativos %.3f" % (false_negatives/total * 100))

print("Total %f" % (sum(class1ExpectedResult.values())))

# teste sala 2
from random import choice
from numpy import load
from numpy import expand_dims
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import Normalizer
from sklearn.svm import SVC
from matplotlib import pyplot

data = load('classification-dataset.npz')
testX_faces = data['arr_2']

data = load('classification-embeddings.npz')
trainX, trainy, testX, testy = data['arr_0'], data['arr_1'], data['arr_2'], data['arr_3']

in_encoder = Normalizer(norm='l2')
trainX = in_encoder.transform(trainX)
testX = in_encoder.transform(testX)

out_encoder = LabelEncoder()
out_encoder.fit(trainy)
trainy = out_encoder.transform(trainy)
testy = out_encoder.transform(testy)

model = SVC(kernel='linear', probability=True)
model.fit(trainX, trainy)


class_faces = extract_faces('/content/drive/MyDrive/PDI/classroom/class2.jpeg')
class1ExpectedResult = {
    "ant_man": False,
    "capitao_america": True,
    "drax": False,
    "falcao": False,
    "gamora": False,
    "gaviao_arqueiro": True,
    "homem_aranha": False,
    "hulk": False,
    "ironman": True,
    "pantera_negra": False,
    "star_lord": False,
    "strange": False,
    "thor": True,
    "viuva_negra": True,
    "wanda": False,
    "war_machine": False
}

class1Results = {
    "ant_man": False,
    "capitao_america": False,
    "drax": False,
    "falcao": False,
    "gamora": False,
    "gaviao_arqueiro": False,
    "homem_aranha": False,
    "hulk": False,
    "ironman": False,
    "pantera_negra": False,
    "star_lord": False,
    "strange": False,
    "thor": False,
    "viuva_negra": False,
    "wanda": False,
    "war_machine": False
}
classroom = list()

model2 = load_model('/content/drive/MyDrive/PDI/facenet_keras.h5')
for face_pixels in class_faces:
	print(face_pixels.shape)
	embedding = get_embedding(model2, face_pixels)
	classroom.append(embedding)
 
classroom = asarray(classroom)
in_encoder = Normalizer(norm='l2')
faces = in_encoder.transform(classroom)
cont = 0
for face in faces:

  samples = expand_dims(face, axis=0)
  yhat_class = model.predict(samples)
  yhat_prob = model.predict_proba(samples)
  class_index = yhat_class[0]
  class_probability = yhat_prob[0,class_index] * 100
  predict_names = out_encoder.inverse_transform(yhat_class)
  title = '%s (%.3f)' % (predict_names[0], class_probability)
  class1Results[predict_names[0]] = True
  cont += 1
print (class1ExpectedResult)
print (class1Results)
total = len(class1ExpectedResult)
corrects = 0
false_positives = 0
false_negatives = 0
for key in class1ExpectedResult:
  if class1Results[key] == class1ExpectedResult[key]: 
    corrects += 1
  elif class1Results[key] == True:
      false_positives += 1
  else: 
      false_negatives += 1 

print("Acertou %.3f" % (corrects/total * 100))
print("Falsos positivos %.3f" % (false_positives/total * 100))
print("Falsos negativos %.3f" % (false_negatives/total * 100))

print("Total %f" % (sum(class1ExpectedResult.values())))

from random import choice
from numpy import load
from numpy import expand_dims
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import Normalizer
from sklearn.svm import SVC
from matplotlib import pyplot

data = load('classification-dataset.npz')
testX_faces = data['arr_2']

data = load('classification-embeddings.npz')
trainX, trainy, testX, testy = data['arr_0'], data['arr_1'], data['arr_2'], data['arr_3']

in_encoder = Normalizer(norm='l2')
trainX = in_encoder.transform(trainX)
testX = in_encoder.transform(testX)

out_encoder = LabelEncoder()
out_encoder.fit(trainy)
trainy = out_encoder.transform(trainy)
testy = out_encoder.transform(testy)

model = SVC(kernel='linear', probability=True)
model.fit(trainX, trainy)


class_faces = extract_faces('/content/drive/MyDrive/PDI/classroom/class3.jpeg')
class1ExpectedResult = {
    "ant_man": False,
    "capitao_america": True,
    "drax": False,
    "falcao": False,
    "gamora": False,
    "gaviao_arqueiro": True,
    "homem_aranha": False,
    "hulk": True,
    "ironman": True,
    "pantera_negra": False,
    "star_lord": False,
    "strange": False,
    "thor": True,
    "viuva_negra": True,
    "wanda": False,
    "war_machine": False
}

class1Results = {
    "ant_man": False,
    "capitao_america": False,
    "drax": False,
    "falcao": False,
    "gamora": False,
    "gaviao_arqueiro": False,
    "homem_aranha": False,
    "hulk": False,
    "ironman": False,
    "pantera_negra": False,
    "star_lord": False,
    "strange": False,
    "thor": False,
    "viuva_negra": False,
    "wanda": False,
    "war_machine": False
}
classroom = list()

model2 = load_model('/content/drive/MyDrive/PDI/facenet_keras.h5')
for face_pixels in class_faces:
	print(face_pixels.shape)
	embedding = get_embedding(model2, face_pixels)
	classroom.append(embedding)
 
classroom = asarray(classroom)
in_encoder = Normalizer(norm='l2')
faces = in_encoder.transform(classroom)
cont = 0
for face in faces:

  samples = expand_dims(face, axis=0)
  yhat_class = model.predict(samples)
  yhat_prob = model.predict_proba(samples)
  
  class_index = yhat_class[0]
  class_probability = yhat_prob[0,class_index] * 100
  predict_names = out_encoder.inverse_transform(yhat_class)
  
  title = '%s (%.3f)' % (predict_names[0], class_probability)
  class1Results[predict_names[0]] = True
  cont += 1
print (class1ExpectedResult)
print (class1Results)
total = len(class1ExpectedResult)
corrects = 0
false_positives = 0
false_negatives = 0
for key in class1ExpectedResult:
  if class1Results[key] == class1ExpectedResult[key]: 
    corrects += 1
  elif class1Results[key] == True:
      false_positives += 1
  else: 
      false_negatives += 1 

print("Acertou %.3f" % (corrects/total * 100))
print("Falsos positivos %.3f" % (false_positives/total * 100))
print("Falsos negativos %.3f" % (false_negatives/total * 100))

print("Total %f" % (sum(class1ExpectedResult.values())))

from random import choice
from numpy import load
from numpy import expand_dims
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import Normalizer
from sklearn.svm import SVC
from matplotlib import pyplot

data = load('classification-dataset.npz')
testX_faces = data['arr_2']

data = load('classification-embeddings.npz')
trainX, trainy, testX, testy = data['arr_0'], data['arr_1'], data['arr_2'], data['arr_3']

in_encoder = Normalizer(norm='l2')
trainX = in_encoder.transform(trainX)
testX = in_encoder.transform(testX)

out_encoder = LabelEncoder()
out_encoder.fit(trainy)
trainy = out_encoder.transform(trainy)
testy = out_encoder.transform(testy)

model = SVC(kernel='linear', probability=True)
model.fit(trainX, trainy)


class_faces = extract_faces('/content/drive/MyDrive/PDI/classroom/class4.jpeg')
class1ExpectedResult = {
    "ant_man": False,
    "capitao_america": True,
    "drax": False,
    "falcao": False,
    "gamora": False,
    "gaviao_arqueiro": True,
    "homem_aranha": False,
    "hulk": True,
    "ironman": False,
    "pantera_negra": False,
    "star_lord": False,
    "strange": False,
    "thor": True,
    "viuva_negra": True,
    "wanda": False,
    "war_machine": False
}

class1Results = {
    "ant_man": False,
    "capitao_america": False,
    "drax": False,
    "falcao": False,
    "gamora": False,
    "gaviao_arqueiro": False,
    "homem_aranha": False,
    "hulk": False,
    "ironman": False,
    "pantera_negra": False,
    "star_lord": False,
    "strange": False,
    "thor": False,
    "viuva_negra": False,
    "wanda": False,
    "war_machine": False
}
classroom = list()

model2 = load_model('/content/drive/MyDrive/PDI/facenet_keras.h5')
for face_pixels in class_faces:
	print(face_pixels.shape)
	embedding = get_embedding(model2, face_pixels)
	classroom.append(embedding)
 
classroom = asarray(classroom)
in_encoder = Normalizer(norm='l2')
faces = in_encoder.transform(classroom)
cont = 0
for face in faces:
  
  samples = expand_dims(face, axis=0)
  yhat_class = model.predict(samples)
  yhat_prob = model.predict_proba(samples)
  
  class_index = yhat_class[0]
  class_probability = yhat_prob[0,class_index] * 100
  predict_names = out_encoder.inverse_transform(yhat_class)
  
  title = '%s (%.3f)' % (predict_names[0], class_probability)
  class1Results[predict_names[0]] = True
  cont += 1
print (class1ExpectedResult)
print (class1Results)
total = len(class1ExpectedResult)
corrects = 0
false_positives = 0
false_negatives = 0
for key in class1ExpectedResult:
  if class1Results[key] == class1ExpectedResult[key]: 
    corrects += 1
  elif class1Results[key] == True:
      false_positives += 1
  else: 
      false_negatives += 1 

print("Acertou %.3f" % (corrects/total * 100))
print("Falsos positivos %.3f" % (false_positives/total * 100))
print("Falsos negativos %.3f" % (false_negatives/total * 100))

print("Total %f" % (sum(class1ExpectedResult.values())))

from random import choice
from numpy import load
from numpy import expand_dims
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import Normalizer
from sklearn.svm import SVC
from matplotlib import pyplot

data = load('classification-dataset.npz')
testX_faces = data['arr_2']

data = load('classification-embeddings.npz')
trainX, trainy, testX, testy = data['arr_0'], data['arr_1'], data['arr_2'], data['arr_3']

in_encoder = Normalizer(norm='l2')
trainX = in_encoder.transform(trainX)
testX = in_encoder.transform(testX)

out_encoder = LabelEncoder()
out_encoder.fit(trainy)
trainy = out_encoder.transform(trainy)
testy = out_encoder.transform(testy)

model = SVC(kernel='linear', probability=True)
model.fit(trainX, trainy)


class_faces = extract_faces('/content/drive/MyDrive/PDI/classroom/class5.jpg')
class1ExpectedResult = {
    "ant_man": False,
    "capitao_america": True,
    "drax": True,
    "falcao": False,
    "gamora": True,
    "gaviao_arqueiro": True,
    "homem_aranha": False,
    "hulk": True,
    "ironman": True,
    "pantera_negra": True,
    "star_lord": True,
    "strange": False,
    "thor": True,
    "viuva_negra": True,
    "wanda": False,
    "war_machine": False
}

class1Results = {
    "ant_man": False,
    "capitao_america": False,
    "drax": False,
    "falcao": False,
    "gamora": False,
    "gaviao_arqueiro": False,
    "homem_aranha": False,
    "hulk": False,
    "ironman": False,
    "pantera_negra": False,
    "star_lord": False,
    "strange": False,
    "thor": False,
    "viuva_negra": False,
    "wanda": False,
    "war_machine": False
}
classroom = list()

model2 = load_model('/content/drive/MyDrive/PDI/facenet_keras.h5')
for face_pixels in class_faces:
	print(face_pixels.shape)
	embedding = get_embedding(model2, face_pixels)
	classroom.append(embedding)
 
classroom = asarray(classroom)
in_encoder = Normalizer(norm='l2')
faces = in_encoder.transform(classroom)
cont = 0
for face in faces:
  
  samples = expand_dims(face, axis=0)
  yhat_class = model.predict(samples)
  yhat_prob = model.predict_proba(samples)
 
  class_index = yhat_class[0]
  class_probability = yhat_prob[0,class_index] * 100
  predict_names = out_encoder.inverse_transform(yhat_class)
  
  title = '%s (%.3f)' % (predict_names[0], class_probability)
  class1Results[predict_names[0]] = True
  cont += 1
print (class1ExpectedResult)
print (class1Results)
total = len(class1ExpectedResult)
corrects = 0
false_positives = 0
false_negatives = 0
for key in class1ExpectedResult:
  if class1Results[key] == class1ExpectedResult[key]: 
    corrects += 1
  elif class1Results[key] == True:
      false_positives += 1
  else: 
      false_negatives += 1 

print("Acertou %.3f" % (corrects/total * 100))
print("Falsos positivos %.3f" % (false_positives/total * 100))
print("Falsos negativos %.3f" % (false_negatives/total * 100))

print("Total %f" % (sum(class1ExpectedResult.values())))