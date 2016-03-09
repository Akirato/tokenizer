#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
import re
import sys,codecs
import operator
import matplotlib.pyplot as plt
from collections import Counter
def regex_or(*items):
    return '(?:' + '|'.join(items) + ')'

#Exception Kind of Strings:
Contractions = re.compile(u"(?i)(\w+)(n['’′]t|['’′]ve|['’′]ll|['’′]d|['’′]re|['’′]s|['’′]m)$", re.UNICODE)
Whitespace = re.compile(u"[\s\u0020\u00a0\u1680\u180e\u202f\u205f\u3000\u2000-\u200a]+", re.UNICODE)
punctChars = r"['\"“”‘’.?!…,:;]"
punctSeq   = r"['\"“”‘’]+|[.?!,…]+|[:;]+"
entity     = r"&(?:amp|lt|gt|quot);"
urlStart1  = r"(?:https?://|\bwww\.)"
commonTLDs = r"(?:com|org|edu|gov|net|mil|biz|in|ac|abc|xyz)"
urlStart2  = r"\b(?:[A-Za-z\d-])+(?:\.[A-Za-z0-9]+){0,3}\." + regex_or(commonTLDs)
urlBody    = r"(?:[^\.\s<>][^\s<>]*?)?"
urlExtraBeforeEnd = regex_or(punctChars, entity) + "+?"
urlEnd     = r"(?:\.\.+|[<>]|\s|$)"
url        = regex_or(urlStart1, urlStart2) + urlBody + "(?=(?:"+urlExtraBeforeEnd+")?"+urlEnd+")"
timeLike   = r"\d+(?::\d+){1,2}"
numberWithCommas = r"(?:(?<!\d)\d{1,3},)+?\d{3}" + r"(?=(?:[^,\d]|$))"
endsWithoutStops = regex_or("$", r"\s", r"[“\"?!,:;]", entity)
aa1  = r"(?:[A-Za-z]\.){2,}(?=" + endsWithoutStops + ")"
aa2  = r"[^A-Za-z](?:[A-Za-z]\.){1,}[A-Za-z](?=" + endsWithoutStops + ")"
standardAbbreviations = r"\b(?:[Mm]r|[Mm]rs|[Mm]s|[Dd]r|[Ss]r|[Jj]r|[Rr]ep|[Ss]en|[Ss]t)\."
arbitraryAbbrev = regex_or(aa1, aa2, standardAbbreviations)
separators  = "(?:--+|―|—|~|–|=)"
thingsThatSplitWords = r"[^\s\.,?\"]"
embeddedApostrophe = thingsThatSplitWords+r"+['’′]" + thingsThatSplitWords + "*"
Bound = r"(?:\W|^|$)"
Email = regex_or("(?<=(?:\W))", "(?<=(?:^))") + r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}(?=" +Bound+")"

dontChange  = re.compile(
    unicode(regex_or(url,Email,timeLike,numberWithCommas,\
        entity,punctSeq,arbitraryAbbrev,separators,\
        embeddedApostrophe).decode('utf-8')), re.UNICODE)

#Punctuations:
edgePunctChars    = u"'\"“”‘’«»{}\\(\\)\\[\\]\\*&"
edgePunct    = "[" + edgePunctChars + "]"
notEdgePunct = "[a-zA-Z0-9]"
offEdge = r"(^|$|:|;|\s|\.|,)" 
EdgePunctLeft  = re.compile(offEdge + "("+edgePunct+"+)("+notEdgePunct+")", re.UNICODE)
EdgePunctRight = re.compile("("+notEdgePunct+")("+edgePunct+"+)" + offEdge, re.UNICODE)

def splitToken(token):
    m = Contractions.search(token)
    if m:
        return [m.group(1), m.group(2)]
    return [token]

def splitEdgePunct(input):
    input = EdgePunctLeft.sub(r"\1\2 \3", input)
    input = EdgePunctRight.sub(r"\1 \2\3", input)
    return input

def addAllnonempty(master, smaller):
    for s in smaller:
        strim = s.strip()
        if (len(strim) > 0):
            master.append(strim)
    return master

def simpleTokenize(text):
    #start with punctuations, no effect on text
    splitPunctText = splitEdgePunct(text) 
    textLength = len(splitPunctText)

    # Now going to the regex we have globally
    nosplitter = []
    nosplitterBorders = []
    for match in dontChange.finditer(splitPunctText):
        # "nosplitter" should not be split at any instance. Seriously nowhere!!!!
        if (match.start() != match.end()):# just for insurance
            nosplitter.append( [splitPunctText[match.start():match.end()]] )
            nosplitterBorders.append( (match.start(), match.end()) )

    indices = [0]
    for (first, second) in nosplitterBorders:
        indices.append(first)
        indices.append(second)
    indices.append(textLength)
    splitGoods = []
    for i in range(0, len(indices), 2):
        goodstr = splitPunctText[indices[i]:indices[i+1]]
        splitstr = goodstr.strip().split(" ")
        splitGoods.append(splitstr)
    zippedStr = []
    for i in range(len(nosplitter)):
        zippedStr = addAllnonempty(zippedStr, splitGoods[i])
        zippedStr = addAllnonempty(zippedStr, nosplitter[i])
    zippedStr = addAllnonempty(zippedStr, splitGoods[len(nosplitter)])
    return zippedStr

def squeezeWhitespace(input):
    return Whitespace.sub(" ", input).strip()

def splitSlash(token):
     words = token.split('/')
     newToken = []
     if len(words) == 1:
         return token
     for word in words:
         if not word.isdigit():
             for word in words:
                 newToken.append(word)
                 newToken.append('/')
             return newToken[:-1]
     return token
                 
def tokenize(text):
    tokens = simpleTokenize(squeezeWhitespace(text))
    finalTokens = []
    for token in tokens:
        if '/' in token:
            for sS in splitSlash(token):
                finalTokens.append(sS)
        else:
            for sT in splitToken(token):
                 finalTokens.append(sT)
    return finalTokens

def makeBigrams(unigrams):
    bigrams = []
    for i in range(0,len(unigrams)-1):
        bigrams.append((unigrams[i],unigrams[i+1]))
    return bigrams

def makeTrigrams(unigrams):
    trigrams = []
    for i in range(0,len(unigrams)-2):
        trigrams.append((unigrams[i],unigrams[i+1],unigrams[i+2]))
    return trigrams

        
def plot(points):
    plt.plot(points[:1000])
    plt.xlabel('Words')
    plt.ylabel('Frequency')
    plt.show()


if __name__=="__main__":
    if len(sys.argv)<2:
        lines = [':Please yes.','I am a good boy.','I was born on 12-09-1990 at 23:34:45','I am going to http://google.com and https://iiit.ac.in']
        for i in lines:
            print(i)
            print(tokenize(i))
    elif len(sys.argv) == 2:
        fil = sys.argv[1]
        data = open(fil,'rb').read()
    elif len(sys.argv) > 2:
        fil = codecs.open(sys.argv[1], 'r', encoding='utf-8')
        data = fil.read()
        tokens = tokenize(data)
        if len(sys.argv) > 4 and sys.argv[4] == 'bigrams':
            tokens = makeBigrams(tokens)
        if len(sys.argv) > 4 and sys.argv[4] == 'trigrams':
            tokens = makeTrigrams(tokens)
        fil.close()
        counter = Counter(tokens)
        sorted_counter = (sorted(counter.items(), key=operator.itemgetter(1)))[::-1]
        if len(sys.argv) > 3 and sys.argv[3] == 'plotAndWrite':
            fil2 = codecs.open(sys.argv[2],'w', encoding='utf-8')
            points = []
            for i in sorted_counter:
                points.append(i[1])
                if len(sys.argv) > 4 and sys.argv[4] == 'trigrams':
                    fil2.write("('"+i[0][0]+"' , '"+i[0][1]+"' , '"+i[0][2]+"')"+'\t'+str(i[1])+'\n')
                elif len(sys.argv) > 4 and sys.argv[4] == 'bigrams':
                    fil2.write("('"+i[0][0]+"' , '"+i[0][1]+"')"+'\t'+str(i[1])+'\n')
                elif len(sys.argv) > 4:
                    fil2.write("('"+i[0][0]+"')"+'\t'+str(i[1])+'\n')
            fil2.close()
            plot(points)
        if len(sys.argv) > 3 and sys.argv[3] == 'plot':
            points = []
            for i in sorted_counter:
                points.append(i[1])
            plot(points)
        if len(sys.argv) > 3 and sys.argv[3] == 'write':
            fil2 = codecs.open(sys.argv[2],'w', encoding='utf-8')
            for i in sorted_counter:
                if len(sys.argv) > 4 and sys.argv[4] == 'trigrams':
                    fil2.write("('"+i[0][0]+"' , '"+i[0][1]+"' , '"+i[0][2]+"')"+'\t'+str(i[1])+'\n')
                elif len(sys.argv) > 4 and sys.argv[4] == 'bigrams':
                    fil2.write("('"+i[0][0]+"' , '"+i[0][1]+"')"+'\t'+str(i[1])+'\n')
                elif len(sys.argv) > 4:
                    fil2.write("('"+i[0][0]+"')"+'\t'+str(i[1])+'\n')
            fil2.close()



      
