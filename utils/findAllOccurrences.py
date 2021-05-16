def findAllOccurrences(string, target):
    indexes = [i for i in range(len(string)) if string.startswith(target, i)]
    return max(indexes)