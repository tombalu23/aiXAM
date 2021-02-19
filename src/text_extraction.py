import textract

def extractText(filePath):
    text = textract.process(filePath)
    text = text.decode("utf8")
    formatted_text = str(text.replace('\\n', ' '))
    # print(formatted_text)
    return formatted_text

#Txt file
filePath = "./corpus/gravity.txt"
print(extractText(filePath))

#PDF file
filePath = "./corpus/ncert_economics_Chapter4.pdf"
print(extractText(filePath))

