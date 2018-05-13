# pykarta/geocoder/massgis.py
# Copyright 2013--2018, Trinity College Computing Center
# Last modified: 13 May 2018

import lxml.etree as ET
from geocoder_base import GeocoderBase, GeocoderResult, GeocoderError
import pykarta.address

# https://wiki.state.ma.us/confluence/pages/viewpage.action?pageId=451772508

class GeocoderMassGIS(GeocoderBase):
	url_server = "gisprpxy.itd.state.ma.us"
	url_path = "/MassGISCustomGeocodeLatLongApplication/MassGISCustomGeocodeService.asmx"
	delay = 1.0		# no more than one request per second

	def FindAddr(self, address, countrycode=None):
		result = GeocoderResult(address, "MassGIS")
		if address[self.f_state] in ("MA", "CT", "NY", "NH", "VT"):	# covers these states in whole or in part
			self.FindAddr2(address, result)
		if result.coordinates is None:
			self.debug("  No match")
		return result

	def FindAddr2(self, address, result):
		query = ET.Element("{http://schemas.xmlsoap.org/soap/envelope/}Envelope",
			# This is an LXML feature
			nsmap={
				"soap":"http://schemas.xmlsoap.org/soap/envelope/",
				"xsi":"http://www.w3.org/2001/XMLSchema-instance",
				"xsd":"http://www.w3.org/2001/XMLSchema",
				}
			)

		query_body = ET.Element("{http://schemas.xmlsoap.org/soap/envelope/}Body")
		query.append(query_body)

		query_address = ET.Element("GeocodeAddress", nsmap={None:"http://tempuri.org/"})
		query_body.append(query_address)

		query_term = ET.Element("Address")
		abbr_street = pykarta.address.abbreviate_street(address[self.f_street])
		query_term.text = "%s %s" % (address[self.f_house_number], abbr_street)
		query_address.append(query_term)

		query_term = ET.Element("City")
		query_term.text = address[self.f_city]
		query_address.append(query_term)

		query_term = ET.Element("State")
		query_term.text = address[self.f_state]
		query_address.append(query_term)

		if address[self.f_postal_code] != "":
			query_term = ET.Element("ZipCode")
			query_term.text = address[self.f_postal_code]
			query_address.append(query_term)

		# xml_declaration and pretty_print require LXML
		query_text = ET.tostring(ET.ElementTree(element=query), encoding="utf-8", xml_declaration=True, pretty_print=True)
		#print query_text

		resp_text = self.get(self.url_path, query=query_text, method="POST", content_type="text/xml")
		#print resp_text
		try:
			tree = ET.XML(resp_text)
		except:
			self.debug("  Invalid response")
			return result

		self.debug_indented(ET.tostring(tree, encoding="utf-8", pretty_print=True))

		match = tree.find(".//{http://tempuri.org/}GeocodeAddressResult")
		score = match.find("{http://tempuri.org/}Score")
		if score is not None:
			score = score.text
			matched_address = match.find("{http://tempuri.org/}MatchedAddress").text
			lat = float(match.find("{http://tempuri.org/}Lat").text)
			lon = float(match.find("{http://tempuri.org/}Long").text)
			#print score, lat, lon
			if score == "100" and matched_address.startswith("%s %s," % (address[self.f_house_number], abbr_street.upper())):
				result.coordinates = (lat, lon)
				result.precision = "INTERPOLATED"
			else:
				result.alternative_addresses.append(matched_address)

if __name__ == "__main__":
	gc = GeocoderMassGIS()
	gc.debug_enabled = True
	print gc.FindAddr(["457","Union Street","","West Springfield","MA",""])
	#print gc.FindAddr(["10","Improbable Street","","Westfield","MA","01085"])
	#print gc.FindAddr(["32","Park Avenue Court","","West Springfield","MA",""])

