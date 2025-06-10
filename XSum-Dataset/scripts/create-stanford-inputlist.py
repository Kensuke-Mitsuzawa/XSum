import os
import codecs


PATH_DIR_INPUT_FILES = "./xsum-extracts-from-downloads"
PATH_OUTCOME_LIST_FILE = "./stanford-corenlp-full-2015-12-09/stanford-inputlist.txt"



def list_files_to_file(directory_path, output_filename):
    """
    Lists all files (not directories) in the specified directory and writes
    their full paths to an output text file.

    Args:
        directory_path (str): The path to the directory to scan.
        output_filename (str, optional): The name of the output text file.
                                         Defaults to "file_list.txt".
    """

    # Check if the directory exists
    if not os.path.isdir(directory_path):
        raise Exception("Error: Directory '%s' does not exist." % directory_path)
    # end if

    assert os.path.exists(os.path.dirname(output_filename)), "The outcome direcoty does not exist: %s" % os.path.pardir(output_filename)

    file_paths = []
    # os.listdir() gets all entries (files and directories)
    for entry_name in os.listdir(directory_path):
        full_path = os.path.join(directory_path, entry_name)
        # Check if it's a file (and not a directory)
        if os.path.isfile(full_path):
            file_paths.append(full_path)

    # Write the list of file paths to the output file
    with open(output_filename, 'w') as f:
        for path in file_paths:
            f.write(os.path.abspath(path) + '\n')

    print "Successfully listed %d files from '%s' to '%s'." % (len(file_paths), directory_path, output_filename)

# end def

list_files_to_file(PATH_DIR_INPUT_FILES, PATH_OUTCOME_LIST_FILE)
