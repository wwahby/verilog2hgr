import argparse
import re


class Map_1to1:
	def __init__(self):
		self.d = {}
		self.num_elements = 0

	def add(self, k, v):
		if ( (k not in self.d) and (v not in self.d) ):
			self.d[k] = v
			self.d[v] = k
			self.num_elements += 1

	def rem(self, k):
		if (k in d):
			d.pop(d.pop(k))
			self.num_elements -= 1

class Map_NameToInd:
	def __init__(self):
		self.d = {}
		self.num_elements = 0

	def add(self, k):
		if (k not in self.d):
			new_ind = self.num_elements + 1
			self.d[k] = new_ind
			self.d[new_ind] = k
			self.num_elements += 1
		else:
			new_ind = self.d[k]

		return new_ind

	def rem(self, k):
		if (k in d):
			d.pop(d.pop(k))
			self.num_elements -= 1

	def get(self, k):
		return self.d[k]


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("infile", type=str, help="Input File")
	#parser.add_argument("top_module", type=str, help="Top module in design")
	args = parser.parse_args()

	infile = args.infile
	parse_verilog(infile)


def get_full_line(infile):
	end_of_line_found = False

	full_line = ""
	while (not end_of_line_found):
		new_line = infile.readline()
		new_line = new_line.strip()

		if (new_line[-1] == ";"):
			end_of_line_found = True

		full_line = full_line + " " + new_line

	return full_line


def parse_verilog(infile):

	keep_going = True
	wire_map = Map_NameToInd()
	component_map = Map_NameToInd()
	component_type_dict = {}

	bus_declaration_re = re.compile("[(\d+):(\d+)]")
	wire_tag_list = ["input", "output", "inout", "wire"]
	punctuation_list = [",", ";"]

	while(keep_going):
		element_string = get_full_line(infile)
		if (element_string == ""):
			# stop when we hit the end of the file
			keep_going = False
		else:
			element_arr = element_string.split()
			tag = element_arr[0]

			# if this line corresponds to a wire or an IO, add it to the wire map
			if (tag in wire_tag_list):
				first_element = 1

				# Check for a bus declaration. If we find a bus, then store the min and max wire numbers and move on to the next element in our array
				bus_found = bus_declaration_re.match(element_arr[first_element])
				if(bus_found):
					bus_max = int(bus_found.group(1))
					bus_min = int(bus_found.group(2))
					first_element += 1

				# Accumulate the rest of the elements in this line
				for element_name in element_arr[first_element:]:
					# Remove the last character if it's not actually part of the name
					if (element_name[-1] in punctuation_list):
						element_name = element_name[0:-1]

					# Skip elements which have been completely removed by the punctuation check
					if ( len(element_name) > 0 ):

						# If we have a bus, we need to add all the appropriate wires to the wire list
						# bus wires will be added as element_name[element_ind]
						# multibuses will be added as element_name[element_ind_1][element_ind_2] etc
						if (bus_found):
							for bus_ind in range(bus_min,bus_max+1):
								final_element_name = element_name + "[" + str(bus_ind) + "]"
								wire_map.add(final_element_name)


			else: # tag not in wire_tag_list, therefore we're reading an actual component
				# tag is the component_type
				component_type = tag
				full_component_string = "".join(element_arr[1:])
				component_arr = full_component_string.split(".")

				component_name = component_arr[0].replace("(","")
				for element in component_arr:
					new_element = element.replace("(","")
					new_element = new_element.replace(")","")
					new_element = new_element.replace(",","")
					new_element = new_element.replace(";","")
					new_element_arr = new_element.split()
					wire_name = new_element_arr[1]
					wire_ind = wire_map.get(wire_name)

					# [TODO] Need to add this component to the appropriate nets
					# [TODO] Need to actually have lists of components for each net



