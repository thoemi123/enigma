
def html_extractor(input_soup, css_snippet):
	"""extract specific html elements and store elements as text in a list"""
	elements_text = []
	elements = input_soup.select(css_snippet)
	for elem in elements:
		elements_text.append(elem.get_text())
		return(elements_text)
