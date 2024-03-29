import numpy as np
from sklearn.preprocessing import PolynomialFeatures
import pandas as pd
import os
import re
from sklearn.cluster import KMeans

def load_data(f):
  raw = pd.read_csv(f, converters = {'Id' : lambda x: x.split('_')} )
  user_movie = pd.DataFrame(raw.Id.tolist(), columns = ['user', 'movie'])
  data = pd.concat([user_movie, raw], axis=1)
  data.drop(columns = ["Id"], inplace = True)
  data.rename(columns = { 'Prediction' : 'rating' }, inplace = True)
  return data

def gen_submission(f_name, algo):
  submission = pd.read_csv("data/sample_submission.csv")
  submission['Prediction'] = [int(round(algo.predict(user, movie).est)) for [user, movie] in submission['Id'].str.split('_')]
  submission.to_csv(f_name, index=False)

# algos = [(algo, weight), i.e. (algo1, 0.5)]
def gen_submission_multi(f_name, algos):
  def process(user, movie):
    return sum([algo.predict(user, movie).est * weight for (algo, weight) in algos])

  submission = pd.read_csv("data/sample_submission.csv")
  submission['Prediction'] = [int(round(process(user, movie))) for [user, movie] in submission['Id'].str.split('_')]
  to_clean_f_name = f_name+".to_clean"
  submission.to_csv(to_clean_f_name, index=False)
  truncate(to_clean_f_name, f_name)
  os.remove(to_clean_f_name)

def gen_submission_multi_poly_features(f_name, predictors, weights, degree = None):
  def process(user, movie):
    predictions = [predictor.predict(user, movie).est for predictor in predictors]
    if degree == None:
        expanded_predictions = predictions
    else:
        poly_features = PolynomialFeatures(degree=degree) 
        reshaped = np.array(predictions).reshape(1,-1) 
        expanded_predictions = poly_features.fit_transform(reshaped) 
        point_wise_mult = np.multiply(expanded_predictions, weights)
        print("predictions ", predictions)
        print("expanded and weights ", expanded_predictions, weights)
        print("point wise mult", point_wise_mult)
    return np.sum(point_wise_mult)

  submission = pd.read_csv("data/sample_submission.csv")
  submission['Prediction'] = [int(round(process(user, movie))) for [user, movie] in submission['Id'].str.split('_')]
  to_clean_f_name = f_name+".to_clean"
  submission.to_csv(to_clean_f_name, index=False)
  truncate(to_clean_f_name, f_name)
 # os.remove(to_clean_f_name)




def gen_submission_multi_with_train(f_name, algos):
  def process(user, movie):
    return sum([algo.predict(user, movie).est * weight for (algo, weight) in algos])

  submission = pd.read_csv("data/data_train.csv")
  submission['Prediction2'] = [int(round(process(user, movie))) for [user, movie] in submission['Id'].str.split('_')]
  submission.to_csv(f_name, index=False)  

def truncate(submission_file_name, out_file_name):
    """changes values that are strictly inferior to 1 to 1 and values strictly superior to 5 to 5"""
    with open(submission_file_name, "r") as f:
        with open(out_file_name, "w") as f_out:
            f_out.write("Id,Prediction\n")
            for line in f:
                m = re.match("(.*,)(-?\d+)", line)
                if m == None:
                    print("No match found for "+ line)
                    continue
                rating = int(m.group(2))
                if rating < 1:
                    rating = 1
                elif rating > 5:
                    rating = 5
                f_out.write(m.group(1) + str(rating)+"\n")

def clusterize(data, n_clusters):
  def fill_movies(users):
    return users.fillna(users.mean())
  mega_matrix = data.pivot(index = 'movie', columns = 'user', values = 'rating').apply(fill_movies, axis=1)
  kmeans = KMeans(n_clusters=n_clusters, random_state=999).fit_predict(mega_matrix.values)
  clusters = pd.DataFrame(data={ 'cluster': kmeans, 'movie': mega_matrix.index })
  cluster_dict = clusters.set_index('movie').to_dict()
  cluster_dict = cluster_dict['cluster']
  clustered = clusters.set_index('movie').join(data.set_index('movie'), how='outer', on='movie')
  clustered_dict = {}
  for i in range(len(clustered['cluster'].unique())):
      clustered_dict[i] = clustered[clustered['cluster'] == i].reset_index().drop(columns=['cluster'])
  return clustered_dict

def reject_cluster(data, n):
  d = pd.DataFrame()
  for k in data:
    if k != n:
      d = d.append(data[k])
  return d