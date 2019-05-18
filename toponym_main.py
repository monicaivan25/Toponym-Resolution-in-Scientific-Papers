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
    tagged_indexed_tokens = []
    sentence = sentence.replace('/', ' ').replace("\\", " ").replace("|", " ").replace("_", " ")
    tokens = nltk.word_tokenize(sentence)
    tagged_tokens = nltk.pos_tag(tokens)

    for i in range(0, len(tagged_tokens)):
        tagged_indexed_tokens.append((i, tagged_tokens[i]))
    return tagged_indexed_tokens


def get_nnp_tokens(tagged_indexed_tokens):
    all_nnp_tokens = []
    for token in tagged_indexed_tokens:
        index = token[0]
        if token[1][1] == 'NNP':
            all_nnp_tokens.append((index, token[1][0]))
    return all_nnp_tokens


def filter_trailing_symbols(tokens):
    tokens = list(filter(lambda token: len(token[1]) > 1 and is_not_int(token[1]), tokens))
    return tokens


def search_wiktionary(token):
    definition = ''
    try:
        word = WiktionaryParser().fetch(token)[0]
        for definitions in word['definitions']:
            for subdefinition in definitions['text']:
                definition += subdefinition + ' '
    except IndexError:
        pass
    return definition


def search_geonames(token, definition):
    location_lemmas = get_location_lemmas()
    definition_lemmas = list(
        map(lambda word: WordNetLemmatizer().lemmatize(word), nltk.word_tokenize(definition)))
    if any(word in location_lemmas for word in definition_lemmas):
        geoname = geocoder.geonames(token, key='mnecarechec')
        print(token, "                  ", geoname.address, '-', geoname.country, ':', geoname.lat, geoname.lng)
        return True
    return False


def longest_match(token, all_nnp_tokens):
    index = token[0]
    copy = token[1]
    for tk in all_nnp_tokens:
        if tk[0] == index + 1:
            index += 1
            copy += " " + tk[1]
    dist = index - token[0] + 1
    # print("longest: ", copy)
    return copy, dist


def main():
    # for file in os.listdir('./detection'):
    #     print(file, ':')
    text_block = get_text_block("/11158130.txt")
    tagged_tokens = get_tagged_tokens(text_block)
    all_nnp_tokens = get_nnp_tokens(tagged_tokens)
    all_nnp_tokens = filter_trailing_symbols(all_nnp_tokens)
    # print(all_nnp_tokens)

    # possible_toponyms = greedy_fill(all_nnp_tokens, tagged_tokens)
    index = 0
    while index < len(all_nnp_tokens):
        definition = ""
        token, dist = longest_match(all_nnp_tokens[index], all_nnp_tokens)
        while dist > 0:
            try:
                definition = lesk(text_block, token, 'n').definition()
            except AttributeError:
                definition = search_wiktionary(token)
            finally:
                ok = search_geonames(token, definition)
            if ok:
                break
            else:
                dist -= 1
                token = "".join(token.split()[:-1])
        index += 1 + dist


main()
