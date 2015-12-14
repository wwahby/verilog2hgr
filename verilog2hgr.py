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
			new_ind = self.num_elements
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
		v = self.d[k]

		return v

class VerilogModule:
	def __init__(self):
		self.wire_connection_list = []
		self.wire_map = Map_NameToInd()
		self.component_map = Map_NameToInd()
		self.module_name = ""

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
	nhgrfile_name = infile_base_name + ".nhgr"
	mapfile_name = infile_base_name + ".map"

	(orig_wire_connection_list, orig_component_map, component_type_dict) = parse_verilog(infile_name)
	(wire_connection_list, component_map) = remove_empty_nets_and_unused_components(orig_wire_connection_list, orig_component_map)
	#(wire_connection_list, component_map, component_type_dict) = parse_verilog(infile_name)
	write_hgr(wire_connection_list, component_map, hgrfile_name)
	write_hgr_with_names(wire_connection_list, component_map, nhgrfile_name)
	write_component_map(component_map, mapfile_name)



def get_full_line(infile):
	end_of_line_found = False
	end_of_file_found = False

	full_line = ""
	while (not end_of_line_found):
		new_line = infile.readline()
		new_line = new_line.strip()

		if len(new_line) > 0:
			if (new_line[-1] == ";"):
				end_of_line_found = True

		full_line = full_line + " " + new_line

	if full_line == "":
		end_of_file_found = True
	return (full_line, end_of_file_found)


def parse_verilog(infile_name):

	wire_map = Map_NameToInd()
	wire_connection_list = []
	component_map = Map_NameToInd()
	component_type_dict = {}

	bus_declaration_re = re.compile("[(\d+):(\d+)]")
	wire_tag_list = ["input", "output", "inout", "wire"]
	ignore_tag_list = ["module", "endmodule", "//"]
	punctuation_list = [",", ";"]

	infile = open(infile_name, 'r')

	full_line = ""
	end_of_line_found = False

	for line in infile:
		if (not end_of_line_found):
			new_line = line
			new_line = new_line.strip()

			if len(new_line) > 0:
				if (new_line[-1] == ";"):
					end_of_line_found = True

			full_line = full_line + " " + new_line

		if end_of_line_found:
			element_string = full_line
			full_line = ""
			end_of_line_found = False

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
				component_name = component_name.strip()
				component_index = component_map.add(component_name)
				component_type_dict[component_name] = component_type

				for element_ind in range(2,len(component_arr)):
					element = component_arr[element_ind]
					# Strip out unwanted characters
					new_element = element.replace("("," ")
					new_element = new_element.replace(")","")
					new_element = new_element.replace(",","")
					new_element = new_element.replace(";","")

					# Break into an array. First element will be IO name, second will be connected wire name
					new_element_arr = new_element.split()
					wire_name = new_element_arr[1]

					# Indicate that this component is connected to this wire
					try:
						wire_ind = wire_map.get(wire_name)
					except KeyError:
						wire_map.add(wire_name)
						wire_connection_list.append([])

					if (component_index not in wire_connection_list[wire_ind]):
						wire_connection_list[wire_ind].append(component_index)

	return (wire_connection_list, component_map, component_type_dict)


def remove_empty_nets_and_unused_components(wire_connection_list, component_map):
	num_nets = len(wire_connection_list)
	num_components = component_map.num_elements


	# Create lists of zeros to track length of each net and number of times each component is used
	component_use_list = [0] * num_components
	net_length_list = [0] * num_nets
	for net_ind in range(len(wire_connection_list)):
		net = wire_connection_list[net_ind]
		net_length = len(net)
		net_length_list[net_ind] = net_length

		if len(net) > 1: # only count components used if they're used on a net that has more than one component
			for component_ind in net:
				component_use_list[component_ind] += 1

	# Now we should have a list of how many times each component is used
	# At this point we need to condense down our component map to only include components that actually matter
	new_component_map = Map_NameToInd()
	new_wire_connection_list = []

	for component_ind in range(num_components):
		if component_use_list[component_ind] > 0: # if this component appears in at least one net at least one other thing connected to it then it is a real component
			component_name = component_map.get(component_ind)
			new_component_map.add(component_name)

	# Process all old nets, convert component IDs for valid components, and only add the new nets to the final net list if they have more than one real component
	# This step is a bit roundabout since we're storing indices instead of names
	# We first need to check that the net is long enough
	# Then that each component is real
	# Then we have to find the component ID for each real component
	# Then we have to ultimately decide whether the new net is actually long enough
	for net_ind in range(num_nets):
		net_length = net_length_list[net_ind]
		net = wire_connection_list[net_ind]
		num_real_components = 0
		new_net = []
		for component_ind in net:
			if component_use_list[component_ind] > 0:
				num_real_components += 1
				component_name = component_map.get(component_ind)
				new_component_ind = new_component_map.get(component_name)
				new_net.append(new_component_ind)

		if len(new_net) > 1:
			new_wire_connection_list.append(new_net)

	return (new_wire_connection_list, new_component_map)



def write_hgr(wire_connection_list, component_map, outfile_name):
	outfile = open(outfile_name, 'w')
	num_components = component_map.num_elements
	num_nets = len(wire_connection_list)

	# first, determine how many nets are connected to more than one thing
	num_nets = 0
	for net in wire_connection_list:
		if len(net) > 0:
			num_nets +=1

	# Write header
	outfile.write("{0:d} {1:d}\n".format(num_nets, num_components))

	for net in wire_connection_list:
		# only write out nets that have more than one component connected
		if len(net) > 0:
			net_str_list = {str(component+1) for component in net} # need to add 1 to all the component indices, since HGR indexing starts at 1, not 0
			net_str = " ".join(net_str_list)
			outfile.write(net_str + "\n")

def write_hgr_with_names(wire_connection_list, component_map, outfile_name):
	outfile = open(outfile_name, 'w')
	num_components = component_map.num_elements
	num_nets = len(wire_connection_list)



	# first, determine how many nets are connected to more than one thing
	num_nets = 0
	for net in wire_connection_list:
		if len(net) > 0:
			num_nets +=1

	# Write header
	outfile.write("{0:d} {1:d}\n".format(num_nets, num_components))

	for net in wire_connection_list:
		# only write out nets that have more than one component connected
		if len(net) > 0:
			net_str_list = {component_map.get(component) for component in net} # need to add 1 to all the component indices, since HGR indexing starts at 1, not 0
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

