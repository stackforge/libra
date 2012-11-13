Code Walkthrough
================

Here we'll highlight some of the more important code aspects.

Server Class
------------
.. py:module:: libra.mgm.mgm

.. py:class:: Server(logger, args)

   This class is the main server activity once it has started in either
   daemon on non-daemon mode.

   :param logger: An instance of :py:class:`logging.logger`
   :param args: An instance of :py:class:`libra.common.options.Options`

   .. py:method:: main()

      Sets the signal handler and then called :py:meth:`check_nodes`

   .. py:method:: check_nodes()

      Runs a check to see if new nodes are needed.  Called once by
      :py:meth:`main` at start and then called by the scheduler.
      It also restarts the scheduler at the end of execution

   .. py:method:: reset_scheduler()

      Uses :py:class:`threading.Timer` to set the next scheduled execution of
      :py:meth:`check_nodes`

   .. py:method:: build_nodes(count, api)

       Builds the required number of nodes determined by
       :py:meth:`check_nodes`.

       :param count: The number of nodes to build
       :param api: A driver derived from the :py:class:`MgmDriver` parent class

   .. py:method:: exit_handler(signum, frame)

      The signal handler function.  Clears the signal handler and calls
      :py:meth:`shutdown`

      :param signum: The signal number
      :param frame: The stack frame

   .. py:method:: shutdown(error)

      Causes the application to exit

      :param error: set to True if an error caused shutdown
      :type error: boolean

Node Class
----------

.. py:module:: libra.mgm.node

.. py:class:: Node(username, password, tenant, auth_url, region, keyname, secgroup, image, node_type)

   This class uses :py:class:`novaclient.client` to manipulate Nova nodes

   :param username: The Nova username
   :param password: The Nova password
   :param tenant: The Nova tenant
   :param auth_url: The Nova authentication URL
   :param region: The Nova region
   :param keyaname: The Nova key name for new nodes
   :param secgroup: The Nova security group for new nodes
   :param image: The Nova image ID for new nodes
   :param node_type: The flavor ID for new nodes

   .. py:method:: build()

      Creates a new Nova node and tests that it is running.  It will poll
      every 3 seconds for 2 minutes to check if the node is running.

      :return: True and status dictionary for success, False and error for fail

MgmDriver Class
---------------

.. py:module:: libra.mgm.drivers.base

.. py:class:: MgmDriver

   The defines the API for interacting with various API servers. Drivers for
   these API servers should inherit from this class and implement the relevant
   API methods that it can support.
   `This is an abstract class and is not meant to be instantiated directly.`

   .. py:method:: get_free_count()

      Gets the number of free nodes.  This is used to calculate if more nodes
      are needed

      :return: the number of free nodes

   .. py:method:: add_node(name, address)

      Adds the node details for a new device to the API server.

      :param name: the new name for the node
      :param address: the new public IP address for the node
      :return: True or False and the JSON response (if any)

   .. py:method:: is_online()

      Check to see if the driver has access to a valid API server

      :return: True or False

   .. py:method:: get_url()

      Gets the URL for the current API server

      :return: the URL for the current API server

Known Drivers Dictionary
------------------------

.. py:data:: known_drivers

   This is the dictionary that maps values for the
   :option:`libra_pool_mgm.py --driver` option
   to a class implementing the driver :py:class:`~MgmDriver` API
   for that API server. After implementing a new driver class, you simply add
   a new entry to this dictionary to plug in the new driver.

