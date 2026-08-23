from parsivar import SpellCheck, FindChunks, FindStems, Normalizer, Tokenizer
# from parsivar import POSTagger
from hazm import Normalizer as HazmNormalizer, word_tokenize as Hazmword_tokenize, stopwords_list
import re

class Preprocessing:
    def __init__(self):
        # self.spell_checker = SpellCheck()
        self.normalizer = Normalizer(pinglish_conversion_needed=True)
        self.tokenizer = Tokenizer()
        self.find_chunker = FindChunks()
        self.normalizer = HazmNormalizer()
        self.stop_words = set(stopwords_list())
        # self.tagger = POSTagger()
        self.stem = FindStems()

    def convert_to_str(self, doc):
        return str(doc)

    def spell_correction(self, doc):
        return self.spell_checker.spell_corrector(doc)

    def normilize(self, doc):
        return self.normalizer.normalize(doc)

    def tokenize(self, doc):
        return self.tokenizer.tokenize_words(doc)

    # def pos_tagger(self, words):
    #     return self.tagger.parse(words)

    def stemming(self, word):
        return self.stem.convert_to_stem(word)

    def chunking(self, tags):
        chunks = self.find_chunker.chunk_sentence(tags)
        return self.find_chunker.convert_nestedtree2rawstring(chunks)

    def remove_face(self, doc):
        return re.sub(r"(:\s?\)|:-\)|\(\s?:|\(-:|:\'\)|:\s?D|8-\)|:\s?\||;\s?\)|:-\*|:-\||:-\(|:\s?P|:-P|:-p|:-b|:-O|:-o|:-0|:-\@|:\$|:-\^|:-&|:-\*|:-\+|:-\~|:-\`|:-\>|:-\<|:-\}|:-\{|\[:\s?\]|\[:\s?\]|:\s?\]|:\s?\[|:\s?\}|:\s?\{)",'',doc)

    def remove_duplicated_character_at_once(self, doc):
        return re.sub(r'(\w)\1{2,}', r'\1', doc)

    def strip_and_lower(self, doc):
        return doc.strip().lower()

    def plain_text_extractor(self, doc):
        text_pattern = r"[\u0600-\u06FF\s,۰-۹,0-9,a-z,A-Z]*"

        final_list = re.findall(text_pattern, doc)

        # Filter out empty strings and join the non-empty strings together
        result_string = ''.join([s for s in final_list if s.strip()])
        return result_string

    def remove_stop_words(self, doc):
        normalized_text = self.normalizer.normalize(doc)

        # Tokenize the text
        tokens = Hazmword_tokenize(normalized_text)

        # Remove punctuation
        tokens_no_punctuation = [token for token in tokens if token.isalpha()]

        # Remove stop words
        filtered_tokens = [token for token in tokens_no_punctuation if token not in self.stop_words]

        # Reconstruct the text
        clean_text = ' '.join(filtered_tokens)
        return clean_text

    def run(self, doc):
        doc = self.convert_to_str(doc)
        doc = self.remove_duplicated_character_at_once(doc)
        doc = self.remove_face(doc)
        # doc = self.spell_correction(doc)
        doc = self.normilize(doc)
        doc = self.strip_and_lower(doc)
        doc = self.plain_text_extractor(doc)
        doc = self.remove_stop_words(doc)
        # words = self.tokenize(doc)

        # words = [self.stemming(word) for word in words]
        # document_tags = self.pos_tagger(words)
        # chuks = self.chunking(document_tags)
        return doc
