def normalizeLineEndings(s):
    return ''.join((line + '\n') for line in s.splitlines())