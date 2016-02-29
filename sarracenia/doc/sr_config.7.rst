===========
 SR_CONFIG 
===========

-------------------------------------
Overview of Sarra Configuration Files
-------------------------------------

:Manual section: 7
:Date: @Date@
:Version: @Version@
:Manual group: Metpx-Sarracenia Suite



SYNOPSIS
========

 - **sr_component** <config> [foreground|start|stop|restart|status]
 - **<config_dir>**/ [ default.conf ]
 - **<config_dir>**/ [ sarra | subscribe | log | sender ] / <config.conf>
 - **<config_dir>**/ scripts / <script.py>


DESCRIPTION
===========

Metpx Sarracenia components are the programs that can be invoked from the command line: 
sr_subscribe, sr_sarra, sr_sender, sr_log, etc...  When any component is invoked, 
a configuration file and an operation are specified.  The operation is one of:

 - foreground:  run a single instance in the foreground logging to stderr
 - restart: stop and then start the configuration.
 - start:  start the configuration running
 - status: check if the configuration is running.
 - stop: stop the configuration from running 

For example:  *sr_subscribe dd foreground* runs the sr_subcribe component with the dd configuration
as a single foreground instance.


Finding Option Files
--------------------

Metpx Sarracenia is configured using a tree of text files using a common
syntax.  The location of config dir is platform dependent (see python appdirs)::

 - linux: ~/.config/sarra
 - Windows: %AppDir%/science.gc.ca/sarra, this might be:
   C:\Users\peter\AppData\Local\science.gc.ca\sarra

The top of the tree contains a file 'default.conf' which contains settings that
are read as defaults for any component on start up.   Individual configuration 
files can be placed anywhere and invoked with the complete path.   When components
are invoked, the provided file is interpreted as a file path (with a .conf
suffix assumed.)  If it is not found as file path, then the component will
look in the component's config directory ( **config_dir** / **component** )
for a matching .conf file.

If it is still not found, it will look for it in the site config dir 
(linux: /usr/share/default/sarra/**component**). 

Finally, if the user has set option **remove_config** to True and if he has
 configured web sites where configurations can be found (option **remote_config_url**),
the program will attempt to download the given named config file from each
site until found.  If successfull, the file will be downloaded into 
**config_dir/Downloads** and interpreted by the program from there.

There is a similar process for all plugins that can be interpreted and executed
within sarracenia programs. In this case the **component** mentionned previously
is set to **plugins**. And before searching in given web sites, the program will
check for a plugins with the given name provided in the sarracenia package.

.. note::
   FIXME: should we keep going to describe http remote loading here... or if we move it elsewhere,
   perhaps move this whole thing to a 'finding config files' section that does the whole job.
   MG  Peter's question still valid... I added more searching descriptions...

Option Syntax
-------------

Options are placed in configuration files, one per line, in the form: 

 **option <value>** 

For example::

  **debug true**

sets the *debug* option to enable more verbose logging.  To provide non-functional 
description of configuration, or comments, use lines that begin with a **#**.  
All options are case sensitive.  **debug** is not the same as **Debug** or **DEBUG**.
Those are three different options (two of which do not exist and will have no effect,
but should generate an ´unknown option warning´.)

Options and command line arguments are equivalent.  Every command line argument 
has a corresponding long version starting with '--'.  For example *-u* has the 
long form *--url*. One can also specify this option in a configuration file. 
To do so, use the long form without the '--', and put its value separated by a space.
The following are all equivalent:

  - **url <url>** 
  - **-u <url>**
  - **--url <url>**

Settings in an individual .conf file are read in after the default.conf
file, and so can override defaults.   Options specified on
the command line override configuration files.

Settings are interpreted in order.  Each file is read from top to bottom.
for example:

sequence #1::

  reject .*\.gif
  accept .*

sequence #2::

  accept .*
  reject .*\.gif


.. note::
   FIXME: does this match only files ending in 'gif' or should we add a $ to it?
   will it match something like .gif2 ? is there an assumed .* at the end?


In sequence #1, all files ending in 'gif' are rejected.  In sequence #2, the accept .* (which
accepts everything) is encountered before the reject statement, so the reject has no effect.


Several options that need to be reused in different config file can be grouped in a file.
In each config where the options subset should appear, the user would then use :

  - **--include <includeConfigPath>**

The includeConfigPath would normally reside under the same config dir of its master configs.
There is no restriction, any option  can be placed in a config file included. The user must
be aware that, for most options, several declarations means overwriting their values.


OPTIONS
=======




CREDENTIALS 
-----------

Ther username and password or keys used to access servers are examples of credentials.
In order to reduce the sensitivity of most configuration files, the credentials
are stored in a single file apart from all other settings.  The credentials.conf file
is the only mandatory configuration file for all users.

For all **sarracenia** programs, the confidential parts of credentials are stored
only in ~/.conf/sarra/credentials.conf.  This includes the destination and the broker
passwords and settings needed by components.  The format is one entry per line.  Examples:

- **amqp://user1:password1@host/**
- **amqps://user2:password2@host:5671/dev**

- **sftp://user5:password5@host**
- **sftp://user6:password6@host:22  ssh_keyfile=/users/local/.ssh/id_dsa**

- **ftp://user7:password7@host  passive,binary**
- **ftp://user8:password8@host:2121  active,ascii**

- **ftps://user7:password7@host  passive,binary,tls**
- **ftps://user8:password8@host:2121  active,ascii,tls,prot_p**

In other configuration files or on the command line, the url simply lacks the
password or key specification.  The url given in the other files is looked
up in credentials.conf.

.. note::
   FIXME: not sure, but the ''additional protocol'' stuff feels out of place here.
   it is like rocket maintenance inserted into a paragraph about baby carriages.
   it is developer info... we leave it here for now, but keep an eye open
   for some place more developerish to move it to.   

To implement support of additional protocols, one would write 
a **_do_download** script.  the scripts would access the credentials 
value in the script with the code :   

- **ok, details = parent.credentials.get(msg.urlcred)**
- **if details  : url = details.url**

The details options are element of the details class (hardcoded):

- **print(details.ssh_keyfile)**
- **print(details.passive)**
- **print(details.binary)**
- **print(details.tls)**
- **print(details.prot_p)**

For the credential that defines protocol for download (upload),
the connection, once opened, is kept opened. It is reset
(closed and reopened) only when the number of downloads (uploads)
reaches the number given by the  **batch**  option (default 100)
 
All download (upload) operations uses a buffer. The size, in bytes,
of the buffer used is given by the **bufsize** option (default 8192)


BROKER
------

All components interact with a broker in some way, so this option will be found
either in the default.conf or each specific configuration file.
The broker option tell each component which broker to contact.

**broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

::
      (default: None and it is mandatory to set it ) 

Once connected to an AMQP broker, the user needs to bind a queue
to exchanges and topics to determine the messages of interest.

To configure in administrative mode, set an option *manager* in the same
format as broker, to specify how to connect to the broker for administrative
purposes.  See Administration Guide for more information.


AMQP QUEUE BINDINGS
-------------------

Once connected to an AMQP broker, the user needs to create a queue and bind it
to an exchange.  These options define which messages (URL notifications) the program receives:

 - **exchange      <name>         (default: xpublic)** 
 - **topic_prefix  <amqp pattern> (default: v00.dd.notify -- developer option)** 
 - **subtopic      <amqp pattern> (subtopic need to be set)** 

In AMQP all messages are published under an **exchange**. 
The exchanges sarracenia use are of type topic.
Each message is publish with its topic string that can be used for filtering.

Several topic options may be declared. To give a correct value to the subtopic,
browse the our website  **http://dd.weather.gc.ca**  and write down all directories of interest.
For each directories write an  **subtopic**  option as follow:

 **subtopic  directory1.*.subdirectory3.*.subdirectory5.#** 

::

 where:  
       *                replaces a directory name 
       #                stands for the remaining possibilities

One has the choice of filtering using  **subtopic**  with only AMQP's limited wildcarding, or the 
more powerful regular expression based  **accept/reject**  mechanisms described below.  The 
difference being that the AMQP filtering is applied by the broker itself, saving the 
notices from being delivered to the client at all. The  **accept/reject**  patterns apply to 
messages sent by the broker to the subscriber.  In other words,  **accept/reject**  are 
client side filters, whereas  **subtopic**  is server side filtering.  

It is best practice to use server side filtering to reduce the number of announcements sent
to the client to a small superset of what is relevant, and perform only a fine-tuning with the 
client side mechanisms, saving bandwidth and processing for all.

topic_prefix is primarily of interest during protocol version transitions, where one wishes to 
specify a non-default protocol version of messages to subscribe to. 

AMQP QUEUE SETTINGS
-------------------

The queue is where the notifications are held on the server for each subscriber.

- **queue_name    <name>         (default: q_<brokerUser>.<programName>.<configName>)** 
- **durable       <boolean>      (default: False)** 
- **expire        <minutes>      (default: None)** 
- **message-ttl   <minutes>      (default: None)** 

By default, components create a queue name that should be unique. The default queue_name
components create follows :  **q_<brokerUser>.<programName>.<configName>** .

**sr_subscribe** is used by several users.  Because we want queue_names to be unique
we feared **queue_name** collision. **sr_subscribe** adds 2 dot separated random values
to the default queue_name and save into file sr_subscribe.<configName>.<brokerUser> 
under his cache directory .cache/sarra/subscribe/<configName>.
On restart/reload ... etc  the queue_name is read from the file and reused.

.. note::
   FIXME:  not clear why sarra does not use the same defaults as subscribe...
   say ddi.edm is asking for stuff, and ddi.dor is asking for stuff, if they make the same
   config file name, they share a queue?  that's actually what we do want, so it turns out
   elegant.  I guess that's the reasoning? hmm... 
   
The  **expire**  option is expressed in minutes... it sets how long should live
a queue without connections The  **durable** option set to True, means writes the queue
on disk if the broker is restarted.
The  **message-ttl**  option set the time in minutes a message can live in the queue.
Past that time, the message is taken out of the queue by the broker.



ROUTING
-------

Sources of data need to indicate the clusters to which they would like data to be delivered.
Data Pumps need to identify themselves, and their neighbors in order to pass data to them.

- **cluster** The name of the local cluster (where data is injected.)

- **cluster_aliases** <alias>,<alias>,...  Alternate names for the cluster.

- **gateway_for** <cluster>,<cluster>,... additional clusters reachable from local pump.

- **to** <cluster>,<cluster>,<cluster>... destination pumps targetted by injectors.

Components which inject data into a network (sr_post, sr_poll, sr_watch) need to set 'to' addresses
for all data injected.  Components which transfer data between bumps, such as sr_sarra and sr_sender, 
interpret *cluster, cluster_aliases*, and *gateway_for*, such that products which are not 
meant for the destination cluster are not transferred.  



DELIVERY SPECIFICATIONS
-----------------------

These options set what files will be downloaded, where they will be placed,
and under which name.

- **accept    <regexp pattern> (must be set)** 
- **directory <path>           (default: .)** 
- **flatten   <boolean>        (default: false)** 
- **inflight  <.string>        (default: .tmp)** 
- **mirror    <boolean>        (default: false)** 
- **overwrite <boolean>        (default: true)** 
- **reject    <regexp pattern> (optional)** 
- **strip     <count>         (default: 0)**
- **accept_unmatch   <boolean> (default: False)**

The  **inflight**  option is a change to the file name used
the download so that other programs reading the directory ignore 
the files until they are complete.  

The modification and taken away when the transfer is complete... 
It is usually a suffix applied to file names, but if **inflight**  is set to  **.**,
then it is prefix, to conform with the standard for "hidden" files on unix/linux.

**Directory** sets where to put the files on your server.
Combined with  **accept** / **reject**  options, the user can select the
files of interest and their directories of residence. (see the  **mirror**
option for more directory settings).

The  **accept**  and  **reject**  options use regular expressions (regexp) to match URL.
Theses options are processed sequentially. 
The URL of a file that matches a  **reject**  pattern is not downloaded.
One that matches an  **accept**  pattern is downloaded into the directory
declared by the closest  **directory**  option above the matching  **accept**  
option.

When using **accept** / **reject**  there might be cases where after
going through all occurences of theses options that the URL was not matched.
The **accept_unmatch** option defines what to do with such a URL. If set to
**True** it will be accepted and **False** rejected.   If no **accept** / **reject**
is specified... the program assumes to accept all URL and will set **accept_unmatch**
to True.

::

  ex.   directory /mylocaldirectory/myradars
        accept    .*RADAR.*

        directory /mylocaldirectory/mygribs
        reject    .*Reg.*
        accept    .*GRIB.*

The  **mirror**  option can be used to mirror the dd.weather.gc.ca tree of the files.
If set to  **True**  the directory given by the  **directory**  option
will be the basename of a tree. Accepted files under that directory will be
placed under the subdirectory tree leaf where it resides under dd.weather.gc.ca.
For example retrieving the following url, with options::

 http://dd.weather.gc.ca/radar/PRECIP/GIF/WGJ/201312141900_WGJ_PRECIP_SNOW.gif

   mirror    True
   directory /mylocaldirectory
   accept    .*RADAR.*

would result in the creation of the directories and the file
/mylocaldirectory/radar/PRECIP/GIF/WGJ/201312141900_WGJ_PRECIP_SNOW.gif

Use the option **strip**  set to N  (an integer) to trim the beginnning of
the directory tree.  For example::

 http://dd.weather.gc.ca/radar/PRECIP/GIF/WGJ/201312141900_WGJ_PRECIP_SNOW.gif

   mirror    True
   strip     3
   directory /mylocaldirectory
   accept    .*RADAR.*

would result in the creation of the directories and the file
/mylocaldirectory/WGJ/201312141900_WGJ_PRECIP_SNOW.gif, stripping out *radar, PRECIP,* and *GIF*
from the path.

The  **flatten**  option is use to set a separator character. This character
replaces the '/' in the url to create a "flattened" filename from its dd.weather.gc.ca path.  
For example, retrieving the following url with options::

 http://dd.weather.gc.ca/model_gem_global/25km/grib2/lat_lon/12/015/CMC_glb_TMP_TGL_2_latlon.24x.24_2013121612_P015.grib2

   flatten   -
   directory /mylocaldirectory
   accept    .*model_gem_global.*

results in the creating ::

 /mylocaldirectory/model_gem_global-25km-grib2-lat_lon-12-015-CMC_glb_TMP_TGL_2_latlon.24x.24_2013121612_P015.grib2


The  **overwrite**  option,if set to false, avoids unnecessary downloads under these conditions :
1- the file to be downloaded is already on the user's file system at the right place and
2- the checksum of the amqp message matches the one of the file.
The default is True for **sr_subscribe** (overwrite without checking), False for the others.

.. note::
  FIXME: Is it correct for this to be different for sr_subscribe? why is default not False everywhere?


LOGS
----

Components write to log files, which by default are found in ~/.cache/sarra/var/log/<component>_<config>_<instance>.log.
at the end of the day, These logs are rotated automatically by the components, and the old log gets a date suffix.
The directory in which the logs are stored can be overridden by the **log** option, and the number of days' logs to keep 
is set by the 'logrotate' parameter.  Log files older than **logrotate** days are deleted.

- **debug**  setting option debug is identical to use  **loglevel debug**

- **log** the directory to store log files in.  Default value: ~/.cache/sarra/var/log (on Linux) 

- **logrotate** the number of days' log files to keep online, assuming a daily rotation.

- **loglevel** the level of logging as expressed by python's logging. 
               possible values are :  critical, error, info, warning, debug.

Note: for **sr-post** only,  option **log** should be a logfile

.. note::
   FIXME:  I don't understand the point of logging a post... it seems like it should always be 'foreground'
   and that it would just write to stderr... it is a one-time thing... confused. what would it log?

   FIXME: We need a verbosity setting. should probably be documented here.  on INFO, the logs are way over the top
   verbose.  Probably need to trim that down. log_level?

INSTANCES
---------

Sometimes one instance of a component and configuration is not enough to process & send all available notifications.  

**instances      <integer>     (default:1)**

The instance option allows launching serveral instances of a component and configuration.
When running sr_sender for example, a number of runtime files that are created.
In the ~/.cache/sarra/sender/configName directory::

  A .sr_sender_configname.state         is created, containing the number instances.
  A .sr_sender_configname_$instance.pid is created, containing the PID  of $instance process.

In directory ~/.cache/sarra/var/log::

  A .sr_sender_configname_$instance.log  is created as a log of $instance process.

The logs can be written in another directory than the default one with option :

**log            <directory logpath>  (default:~/.cache/sarra/var/log)**

.. note::  
  FIXME: indicate windows location also... dot files on windows?


.. Note::

  While the brokers keep the queues available for some time, Queues take resources on 
  brokers, and are cleaned up from time to time.  A queue which is not
  accessed and has too many (implementation defined) files queued will be destroyed.
  Processes which die should be restarted within a reasonable period of time to avoid
  loss of notifications.  A queue which is not accessed for a long (implementation dependent)
  period will be destroyed. 

.. Note::
   FIXME  The last sentence is not really right...sr_audit does track the queues'age... 
          sr_audit acts when a queue gets to the max_queue_size and not running ... nothing more.
          

RABBITMQ LOGGING
----------------

For each download, an amqp log message is sent back to the broker.
Should you want to turned them off the option is :

- **log_back <boolean>        (default: true)** 



PLUGIN SCRIPTS
--------------

Metpx Sarracenia provides minimum functionality to deal with the most common cases, but provides
flexibility to override those common cases with user plugins scripts, written in python.  
MetPX comes with a variety of scripts which can act as examples.   

Users can place their own scripts in the script sub-directory 
of their config directory tree.

A user script should be placed in the
 ~/.config/sarra/plugins directory::

There are two varieties of
scripts:  do\_* and on\_*.  Do\_* scripts are used to implement functions, replacing built-in
functionality, for example, to implement additional transfer protocols.  

- do_download - to implement additional download protocols.

- do_poll - to implement additional polling protocols and processes.

- do_send - to implement additional sending protocols and processes.


On\_* scripts are used more often. They allow actions to be inserted to augment the default 
processing for various specialized use cases. The scripts are invoked by having a given 
configuration file specify an on_<event> option. The event can be one of:

- on_file -- When the reception of a file has been completed, trigger followup action.

- on_line -- In **sr_poll** a line from the ls on the remote host is read in.

- on_message -- when an sr_post(7) message has been received.  For example, a message has been received 
  and additional criteria are being evaluated for download of the corresponding file.  if the on_msg 
  script returns false, then it is not downloaded.  (see discard_when_lagging.py, for example,
  which decides that data that is too old is not worth downloading.)

- on_part -- Large file transfers are split into parts.  Each part is transferred separately.
  When a completed part is received, one can specify additional processing.

- on_post -- when a data source (or sarra) is about to post a message, permit customized
  adjustments of the post.

The simplest example of a script: A do_nothing.py script for **on_file**::

  class Transformer(object): 
      def __init__(self):
          pass

      def perform(self,parent):
          logger = parent.logger

          logger.info("I have no effect but adding this log line")

          return True

  transformer  = Transformer()
  self.on_file = transformer.perform

The only arguments the script receives it **parent**, which is an instance of
the **sr_subscribe** class
Should one of these scripts return False, the processing of the message/file
will stop there and another message will be consumed from the broker.
For other events, the last line of the script must be modified to correspond.

More examples are available in the Guide documentation.


EXAMPLES
--------

Here is a short complete example configuration file:: 

  broker amqp://dd.weather.gc.ca/

  subtopic model_gem_global.25km.grib2.#
  accept .*

This above file will connect to the dd.weather.gc.ca broker, connecting as
anonymous with password anonymous (defaults) to obtain announcements about
files in the http://dd.weather.gc.ca/model_gem_global/25km/grib2 directory.
All files which arrive in that directory or below it will be downloaded 
into the current directory (or just printed to standard output if -n option 
was specified.) 

A variety of example configuration files are available here:

 `http://sourceforge.net/p/metpx/git/ci/master/tree/sarracenia/samples/config/ <http://sourceforge.net/p/metpx/git/ci/master/tree/sarracenia/samples/config>`_



SEE ALSO
--------

`sr_log(7) <sr_log.7.html>`_ - the format of log messages.

`sr_post(1) <sr_post.1.html>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.html>`_ - The format of announcement messages.

`sr_sarra(1) <sr_sarra.1.html>`_ - Subscribe, Acquire, and ReAdvertise tool.

`sr_watch(1) <sr_watch.1.html>`_ - the directory watching daemon.

`http://metpx.sf.net/ <http://metpx.sf.net/>`_ - sr_subscribe is a component of MetPX-Sarracenia, the AMQP based data pump.
