from __future__ import annotations

import os
from itertools import product
from random import randint, shuffle
from string import ascii_lowercase

from line_profiler import profile

all_words_file = "all_words.txt"
removed_words_file = "removed_words.txt"

LENGTH = 5
CAN_ADD_OR_REMOVE = True

length_n_words_file = f"length_{LENGTH}_words.txt"
word_list: set[str] = set()


class Word:
	def __init__(self, word: str, prev_word: str | Word | None = None):
		self.word = word
		if isinstance(prev_word, str):
			self.prev_word = Word(word, None)
		elif isinstance(prev_word, Word):
			self.prev_word = prev_word
		elif prev_word is None:
			self.prev_word = None
		else:
			raise TypeError(f"Invalid prev_word type for class Word: {type(prev_word)}")

	def __eq__(self, other: str | Word):
		if isinstance(other, str):
			return self.word == other
		elif isinstance(other, Word):
			return self.word == other.word

	def __hash__(self):
		return hash(self.word)

	def __len__(self):
		return len(self.word)

	def __getitem__(self, index):
		return self.word[index]

	def __str__(self):
		return self.word

	def __repr__(self):
		return f"'{self}'"


def init_word_list() -> set[str]:
	global word_list

	if CAN_ADD_OR_REMOVE:
		with open(all_words_file, "r") as fp:
			all_words = fp.read().strip().split("\n")
		with open(removed_words_file, "r") as fp:
			removed_words = set(fp.read().strip().split("\n"))

		word_list = set(filter(lambda s: s not in removed_words, all_words))
		return

	if not os.path.isfile(length_n_words_file):
		with open(all_words_file, "r") as fp:
			all_words = fp.read().strip().split("\n")
		with open(removed_words_file, "r") as fp:
			removed_words = set(fp.read().strip().split("\n"))
		length_n_words = filter(
			lambda s: len(s) == LENGTH and s not in removed_words, all_words
		)
		with open(length_n_words_file, "w") as fp:
			fp.write("\n".join(length_n_words))

	with open(length_n_words_file, "r") as fp:
		word_list = {Word(s) for s in fp.read().strip().split("\n")}


one_off_cache: dict[str, set[str]] = {}


# @profile
def get_one_off_words(words: set[Word]) -> set[str]:
	one_off_words = set()
	for word in words:
		if word.word in one_off_cache:
			one_off_words.update({Word(s, word) for s in one_off_cache[word.word]})
			continue

		valid_new_words: set[str] = set()
		for c in ascii_lowercase:
			new_words: set[str] = set()
			for i in range(len(word)):
				new_words.add(word[:i] + c + word[i + 1 :])  # replace
			if CAN_ADD_OR_REMOVE:
				new_words.add(c + word.word)
				for i in range(len(word)):
					new_words.add(word[: i + 1] + c + word[i + 1 :])  # add
					new_words.add(word[:i] + word[i + 1 :])  # remove
			valid_new_words.update(new_words & word_list)
		one_off_cache[word.word] = valid_new_words
		one_off_words.update({Word(s, word) for s in valid_new_words})

	return one_off_words


def find_paths_between_words(start_word: str, end_word: str) -> list[list[str]]:
	start_layer = get_one_off_words({Word(start_word)})
	end_layer = get_one_off_words({Word(end_word)})
	intersection = start_layer & end_layer

	prev_length = 0
	while not intersection:
		if len(start_layer) <= len(end_layer):
			start_layer = get_one_off_words(start_layer)
		else:
			end_layer = get_one_off_words(end_layer)
		intersection = start_layer & end_layer

		length = len(start_layer) + len(end_layer)
		if length == prev_length:
			return []
		prev_length = length

	all_paths = []
	for connecting_word in intersection:
		up = next(word for word in start_layer if word == connecting_word)
		up_path = []
		while up.prev_word != None:
			up = up.prev_word
			up_path.append(up.word)

		down = next(word for word in end_layer if word == connecting_word)
		down_path = []
		while down.prev_word != None:
			down = down.prev_word
			down_path.append(down.word)

		path = [*up_path[::-1], connecting_word, *down_path]
		all_paths.append(path)

	return all_paths

def find_longest_path_from_word(start_word: str) -> list[Word]:
	longest_path: list[Word] = []
	longest_path_length: int = 0
	for i, word in enumerate(word_list):
	    paths = find_paths_between_words(start_word, word)
	    if not paths:
	        continue
	    length = len(paths[0])
	    if length > longest_path_length:
	        longest_path = paths[0]
	        longest_path_length = length
	
	return longest_path


def find_longest_path() -> list[Word]:
	longest_path: list[Word] = []
	longest_path_length: int = 0
	for i, start_word in enumerate(word_list):
		for k, end_word in enumerate(word_list):
			paths = find_paths_between_words(start_word, end_word)
			if not paths:
				continue
			length = len(paths[0])
			if length > longest_path_length:
				longest_path = paths[0]
				longest_path_length = length

				index = i * len(word_list) + k
				print(
					f"{index=} {', '.join(str(w) for w in longest_path)} = {longest_path_length}"
				)

	return longest_path


def get_islands():
	islands: list[set] = [{Word("a")}]
	seen_words = islands[0]
	remaining_words = word_list - seen_words

	while True:
		print(len(islands))

		current_island = islands[-1]
		prev_size = len(current_island)
		current_island = get_one_off_words(current_island)
		seen_words.update(current_island)
		remaining_words -= current_island
		size = len(current_island)

		islands[-1] = current_island
		if prev_size == size:
			if not remaining_words:
				break
			islands.append({Word(next(iter(remaining_words)))})

	return islands


# @profile
def main():
	init_word_list()

	# paths = find_paths_between_words("fleeting", "shallows")
	# print(paths[0], len(paths[0]))

	# longest_path = find_longest_path_from_word("cats")
	# print(f"{', '.join(str(w) for w in longest_path)} = {len(longest_path)}")

	longest_path = find_longest_path()
	print(f"{', '.join(str(w) for w in longest_path)} = {len(longest_path)}")

	# islands = get_islands()
	# sorted_islands = sorted(islands, key=lambda island: len(island), reverse=True)
	# for i in range(20):
	# 	print(sorted_islands[i], len(sorted_islands[i]))


if __name__ == "__main__":
	main()
