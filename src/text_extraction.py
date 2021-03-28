import textract
from summarizer import Summarizer

def extractText(filePath):
    text = textract.process(filePath)
    text = text.decode("utf8")
    formatted_text = str(text.replace('\\n', ' '))
    # print(formatted_text)

    return formatted_text

# #Txt file
# filePath = "./corpus/gravity.txt"
# print(extractText(filePath))

# #PDF file
# filePath = "./corpus/ncert_economics_Chapter4.pdf"
# print(extractText(filePath))

def bert_summarizer(text):
    model = Summarizer()
    result = model(text, ratio = 0.5, max_length = 300)
    summary = "".join(result)
    return summary

# model = Summarizer()
# get_corona_summary=open('./corpus/egypt.txt','r').read()
# result = model(get_corona_summary, ratio = 0.6, max_length = 350)
# summary = "".join(result)
# print("SUMMARY: ", summary) 
# print("----------")
# print("Original text: ", get_corona_summary)

