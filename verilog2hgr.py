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
		if (k in self.d):
			self.d.pop(self.d.pop(k))
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
		if (k in self.d):
			self.d.pop(self.d.pop(k))
			self.num_elements -= 1

	def get(self, k):
		return self.d[k]


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("infile", type=str, help="Input File")
	#parser.add_argument("top_module", type=str, help="Top module in design")
	args = parser.parse_args()


	infile_name = args.infile
	infile_name_arr = infile_name.split(".")
	if len(infile_name_arr) > 1:
		infile_base_name = ".".join(infile_name_arr[0:-1])
	else:
		infile_base_name = infile_name_arr[0]

	hgrfile_name = infile_base_name + ".hgr"
	mapfile_name = infile_base_name + ".map"

	(wire_connection_list, component_map, component_type_dict) = parse_verilog(infile_name)
	write_hgr(wire_connection_list, component_map, hgrfile_name)
	write_component_map(component_map, mapfile_name)


def get_full_line(infile):
	end_of_line_found = False

	full_line = ""
	while (not end_of_line_found):
		new_line = infile.readline()
		new_line = new_line.strip()

		if len(new_line) > 0:
			if (new_line[-1] == ";"):
				end_of_line_found = True

		full_line = full_line + " " + new_line

	return full_line


def parse_verilog(infile_name):

	keep_going = True
	wire_map = Map_NameToInd()
	wire_connection_list = []
	component_map = Map_NameToInd()
	component_type_dict = {}

	bus_declaration_re = re.compile("[(\d+):(\d+)]")
	wire_tag_list = ["input", "output", "inout", "wire"]
	ignore_tag_list = ["module", "endmodule", "//"]
	punctuation_list = [",", ";"]

	infile = open(infile_name, 'r')

	while(keep_going):
		element_string = get_full_line(infile)
		if (element_string == ""):
			# stop when we hit the end of the file
			keep_going = False
		else:
			element_arr = element_string.split()
			tag = element_arr[0]

			if (tag in ignore_tag_list):
				pass # do nothing
			# if this line corresponds to a wire or an IO, add it to the wire map
			elif (tag in wire_tag_list):
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
								wire_connection_list.append([])
						else:
							wire_map.add(element_name)
							wire_connection_list.append([])


			else: # tag not in wire_tag_list, therefore we're reading an actual component
				# tag is the component_type
				# We're assuming that ALL wires are already declared and added to the data structures in the previous section
				component_type = tag
				full_component_string = "".join(element_arr[1:]) # has the effect of removing all whitespace from the original line
				component_arr = full_component_string.split(".") # re-splitting on the .'s which indicate each IO of each component

				component_name = component_arr[0].replace("(","")
				component_index = component_map.add(component_name)
				component_type_dict[component_name] = component_type
				for element in component_arr:
					# Strip out unwanted characters
					new_element = element.replace("(","")
					new_element = new_element.replace(")","")
					new_element = new_element.replace(",","")
					new_element = new_element.replace(";","")

					# Break into an array. First element will be IO name, second will be connected wire name
					new_element_arr = new_element.split()
					print(new_element)
					print("\n")
					print(new_element_arr)
					print("\n\n")
					wire_name = new_element_arr[1]

					# Indicate that this component is connected to this wire
					wire_ind = wire_map.get(wire_name)
					if (component_index not in wire_connection_list[wire_ind]):
						wire_connection_list[wire_ind].append(component_index)

	return (wire_connection_list, component_map, component_type_dict)

def write_hgr(wire_connection_list, component_map, outfile_name):
	outfile = open(outfile_name, 'w')
	num_components = component_map.num_elements
	num_nets = len(wire_connection_list)

	outfile.write("{0:d} {1:d}\n".format(num_nets, num_components))

	for net in wire_connection_list:
		net_str_list = {str(component+1) for component in net} # need to add 1 to all the component indices, since HGR indexing starts at 1, not 0
		net_str = " ".join(net_str_list)
		outfile.write(net_str + "\n")

def write_component_map(component_map, outfile_name):
	outfile = open(outfile_name, 'w')
	num_components = component_map.num_elements
	for component_ind in range(num_components):
		component_name = component_map.get(component_ind)
		outfile.write(component_name + "\n")





if ( __name__ == "__main__"):
	main()

