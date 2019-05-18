import nltk
from nltk.stem import WordNetLemmatizer
from nltk.wsd import lesk
import geocoder
from wiktionaryparser import WiktionaryParser
import fnmatch


def is_not_int(s):
    for char in s:
        if char.isdigit():
            return False
    return True


def get_location_lemmas():
    with open('location_lemmas.txt', 'r') as infile:
        location_lemmas = infile.read().splitlines()
    return location_lemmas


def get_text_block(file):
    text_block = ''
    if fnmatch.fnmatch(file, '*.txt'):
        with open("./detection/" + file, "r") as f:
            text_block = f.read()
    return text_block


def get_tagged_tokens(sentence):
    tokens = nltk.word_tokenize(sentence)
    tagged_tokens = nltk.pos_tag(tokens)
    return tagged_tokens


def filter_trailing_symbols(tokens):
    for i in range(0, len(tokens)):
        if '/' in tokens[i]:
            for subtoken in reversed(tokens[i].split('/')):
                tokens.insert(i + 1, subtoken)
            del tokens[i]
    tokens = list(filter(lambda token: len(token) > 1 and is_not_int(token), tokens))
    return tokens


def greedy_fill(all_nnp_tokens, tagged_tokens):
    possible_toponyms = []
    word_list = list(i[0] for i in tagged_tokens)
    index = 0
    while index < len(word_list):

        # print(index)
        word = word_list[index]
        repeat = False
        for i in possible_toponyms:
            if word in i:
                repeat = True
        if not repeat:
            if word in all_nnp_tokens:
                geoname = geocoder.geonames(word, key='mnecarechec')
                if geoname.address:
                    # print(word)
                    distance = 0
                    word_copy = word
                    while True:
                        if word_list[index + distance + 1] in ".,/?!)([]@#$%&^*_+=-\;:\'\"|":
                            break
                        word_copy += " " + word_list[index + distance + 1]
                        geoname = geocoder.geonames(word_copy, key='mnecarechec')
                        if not geoname.address:
                            break
                        distance += 1
                        word = word_copy
                    possible_toponyms.append(word)
                    print(index, word)
                    index += distance
        index += 1
    return possible_toponyms


def main():
    # for file in os.listdir('./detection'):
    #     print(file, ':')
    text_block = get_text_block("/11158130.txt")
    tagged_tokens = get_tagged_tokens(text_block)
    print(tagged_tokens)
    all_nnp_tokens = list(
        set(map(lambda x: x[0], list(filter(lambda x: x[1] == 'NNP', tagged_tokens)))))
    all_nnp_tokens = filter_trailing_symbols(all_nnp_tokens)
    # print(all_nnp_tokens)
    possible_toponyms = greedy_fill(all_nnp_tokens, tagged_tokens)
    for item in possible_toponyms:
        print(item)
    location_lemmas = get_location_lemmas()
    for token in all_nnp_tokens:
        try:
            definition = lesk(all_nnp_tokens, token, 'n').definition()
        except AttributeError:
            definition = ''
            try:
                word = WiktionaryParser().fetch(token)[0]
                for definitions in word['definitions']:
                    for subdefinition in definitions['text']:
                        definition += subdefinition + ' '
            except IndexError:
                pass
        finally:
            # print(token, definition)
            definition_lemmas = list(
                map(lambda word: WordNetLemmatizer().lemmatize(word), nltk.word_tokenize(definition)))
            if any(word in location_lemmas for word in definition_lemmas):
                geoname = geocoder.geonames(token, key='mnecarechec')
                # print(geoname.address, '-', geoname.country, ':', geoname.lat, geoname.lng)


main()
