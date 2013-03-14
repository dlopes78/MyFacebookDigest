import nltk
import itertools
import sys
import random
import pickle

class Classifier(object):
    """classify by looking at a site"""
    def __init__(self, training_set):
        self.training_set = training_set
        self.stopwords = nltk.corpus.stopwords.words("english")
        self.stemmer = nltk.PorterStemmer()
        self.minlength = 7
        self.maxlength = 25

    def text_process_entry(self, example):
        site_text = nltk.clean_html(example[0]).lower()
        original_tokens = itertools.chain.from_iterable(nltk.word_tokenize(w) for w in nltk.sent_tokenize(site_text))
        tokens = original_tokens #+ [' '.join(w) for w in nltk.util.ngrams(original_tokens, 2)]
        tokens = [w for w in tokens if not w in self.stopwords]
        tokens = [w for w in tokens if self.minlength < len(w) < self.maxlength]
        #tokens = [self.stemmer.stem(w) for w in tokens]
        return (tokens, example[1])

    def text_process_all(self, exampleset):
        processed_training_set = [self.text_process_entry(i) for i in self.training_set]
        processed_training_set = filter(lambda x: len(x[0]) > 0, processed_training_set) # remove empty crawls
        processed_texts = [i[0] for i in processed_training_set]
        
        all_words = nltk.FreqDist(itertools.chain.from_iterable(processed_texts))
        features_to_test = all_words.keys()[:5000]
        self.features_to_test = features_to_test

        featuresets = [(self.document_features(d), c) for (d,c) in processed_training_set]
        return featuresets

    def document_features(self, document):
        #document_words = set(document)
        features = {}
        for word in self.features_to_test:
            #features['contains(%s)' % word] = (word in document_words)
            features['contains(%s)' % word] = (word in document)
            #features['occurrencies(%s)' % word] = document.count(word) 
            #features['atleast3(%s)' % word] = document.count(word) > 3
        return features

    def build_classifier(self, featuresets):
        random.shuffle(featuresets)
        cut_point = len(featuresets) / 5
        train_set, test_set = featuresets[cut_point:], featuresets[:cut_point]
        classifier = nltk.NaiveBayesClassifier.train(train_set)
        return (classifier, test_set)

    def run(self):
        featuresets = self.text_process_all(self.training_set)
        classifier, test_set = self.build_classifier(featuresets)
        self.classifier = classifier
        self.test_classifier(classifier, test_set)

    def classify(self, text):
        return self.classifier.classify(self.document_features(text))

    def test_classifier(self, classifier, test_set):
        print nltk.classify.accuracy(classifier, test_set)
        classifier.show_most_informative_features(45)

infile = open('training1_feb12.txt', 'r')
pol = pickle.load(infile)
infile.close()

infile2 = open('training2_feb12.txt', 'r')
rel = pickle.load(infile2)
infile2.close()

infile3 = open('training3_feb12.txt', 'r')
sports = pickle.load(infile3)
infile3.close()

classes = ('politics','relationship','sports')

list1= [(elem,classes[0]) for elem in pol]
list2= [(elem,classes[1]) for elem in rel]
list3= [(elem,classes[2]) for elem in sports]
training_set=[]
training_set.extend(list1)
training_set.extend(list2)
training_set.extend(list3)

# trivial test
test_text = "we love state politics"
test_text2 = "we will celebrate one year marriage"

if __name__ == '__main__':
    classifier = Classifier(training_set)
    classifier.run()
    print "%s -> classified as: %s" % (test_text, classifier.classify(test_text))
    print "%s -> classified as: %s" % (test_text2, classifier.classify(test_text2))

    outfile = open('classifier_feb12.txt', 'w')
    pickle.dump(classifier, outfile)
    outfile.close()
