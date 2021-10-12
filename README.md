Remedy topology mediator for Agile Service Manager --

This script is an example of how to bring topology data from the Remedy CMDB into a
file that can be ingested by the ASM file observer. It creates CI objsects from the
specified CI classes, as well as relevant relationship information for all CIs of 
interest.

To use:

1. Enter the CI classes you would like to load into the ASM topology into the file:

   config/classlist.conf

   Example default classes are included

2. Configure the config/cmdbserver.conf file with your Remedy server, user, and 
   password. User must have the ability to query REST and CMDB data.
3. Execute the bin/getCmdbData.py create the file observer files.
4. Import the generated files (located under "file-observer-files") using the ASM file
   observer. Note that two files are created - one for edges and one for vertices. The
   vertices file MUST BE LOADED before the edges file. Alternatively, you can append
   the edges file to the vertices file as such:

      cat edges\<date\>.json >> vertices\<date\>.json

   and load it all in one shot.

Some items to note:

-- There are functions available that will send objects directly to the ASM REST
   interface rather than writing out to a file. This may be implemented in the future,
   but if you would like to play with it now, you could comment out the sections that
   write out the file observer files and un-comment the sections below which pass 
   each CI and relation to the "createAsmResource" and "createAsmConnection" functions.
   I would expect them to be ok, as they're from another working topology mediator
   (AIX HMC mediator here): 

      https://github.ibm.com/jcress/HMC-Mediator-for-Agile-Service-Manager

   I have not had the time to test them with this mediation code.

-- The code will write out the results of any Remedy REST queries to the log/ 
   directory. This allows you to make changes to config and test the changes without
   constantly hitting the Remedy REST API, making the process much faster. To
   enable reading from json files rather than the REST API, set either or both of the
   following configuration lines into the "config/getSNOWData.props":
   
      readCisFromFile=1
      readRelationshipsFromFile=1

-- A tip for moving the resulting file observer file to a file observer container:
   tar.gz the files before copying to the file observer container. It will save you
   a metric ton of time copying the file to the container. You can then untar.gz
   at the container. 

-- There is a lot of debug output sent to stdout. Sorry about that. Feel free to:

   %s/print/#print/g

-- Let me know if you have questions, recommendations, or issues: jcress@us.ibm.com


      


# RemedyCMDBTopologyMediatorForAsm
