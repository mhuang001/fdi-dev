Þ          Ô                 e     	   ó  !   ý       )        É     å  *   ý  E   (     n  +     4   ´  ?   é    )     ¯  (   ¾     ç  3   ù  <   -  E   j     °  b   0  t    `   	     i	  !   p	     	  $   
     9
     T
  2   j
  J   
     è
  0   û
  -   ,  3   Z  N       Ý  $   ä     	  #     2   4  @   g     ¨  \   .   A file named ``.secret`` is needed by the build and launch commands. This is an example ``.secret``:: Configure First make a virtual environment: If you see error of log file not found, you are running the ``fdi`` docker by mistake. Only the pool server docker has the log. Login the latest built running container: Make the ``httppool`` image Make the images locally Modify ``docker_entrypoint.sh`` if needed. Modify ``fdi/pns/resources/httppool_server_entrypoint.sh`` if needed. More convenience commands Now you can make the ``fdi`` docker easily: Remove the latest built running container and image: Run the ``make`` commands in the package root directory of fdi. Server credentials are set during server start up, when ``pnslocal.py`` config file is loaded. ``pnslocal.py`` and other configuration files are updated by the Entrypoint files (see the table above) when the docker starts. The Entrypoint files uses environment variables, which are set by the command line with ``--env-file`` so that sensitive information are not left on the command line. Specifications Stop the latest built running container: Table of Contents The following pre-made docker images are available: The following shows how to build the docker images yourself. Then install fdi following instructions in :doc:`installation` , e.g. To build ``httppool`` image, modify the ``FROM`` line in ``fdi/pns/resources/httppool_server_2.docker`` to delete ``mhastro/``. Watch ``/var/log/apache2/error-ps.log`` inside the ``httppool`` docker updating (after launching): Project-Id-Version: fdi 
Report-Msgid-Bugs-To: 
POT-Creation-Date: 2021-12-30 09:03+0800
PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE
Last-Translator: FULL NAME <EMAIL@ADDRESS>
Language: zh_CN
Language-Team: zh_CN <LL@li.org>
Plural-Forms: nplurals=1; plural=0
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8
Content-Transfer-Encoding: 8bit
Generated-By: Babel 2.9.1
 æå»ºåå¯å¨å½ä»¤éè¦ä¸ä¸ªåä¸º ``.secret`` çæä»¶ã è¿æ¯ä¸ä¸ªç¤ºä¾ ``.secret``  éç½® é¦ååå»ºä¸ä¸ªèæç¯å¢ï¼ å¦ææ¨çå°æªæ¾å°æ¥å¿æä»¶çéè¯¯ï¼åæ¨éè¯¯å°è¿è¡äº ``fdi`` dockerã åªææ± æå¡å¨ docker ææ¥å¿ã ç»å½ææ°æå»ºçè¿è¡å®¹å¨ï¼ å¶ä½ ``httppool`` å¾å å¨æ¬å°å¶ä½å¾å å¦æéè¦ï¼ä¿®æ¹ ``docker_entrypoint.sh`` ã å¦æå¿è¦å¯ä¿®æ¹ ``fdi/pns/resources/httppool_server_entrypoint.sh``  æ´æ¹ä¾¿çå½ä»¤ ç°å¨ä½ å¯ä»¥è½»æ¾å°å¶ä½ ``fdi`` dockerï¼ å é¤ææ°æå»ºçè¿è¡å®¹å¨åéåï¼ å¨ fdi çåæ ¹ç®å½ä¸è¿è¡ ``make`` å½ä»¤ã æå¡å¨å­æ®å¨æå¡å¨å¯å¨æé´è®¾ç½®ï¼å½ ``pnslocal.py`` éç½®æä»¶è¢«å è½½æ¶ã ``pnslocal.py`` åå¶ä»éç½®æä»¶å¨ docker å¯å¨æ¶ç± Entrypoint æä»¶ï¼è§ä¸è¡¨ï¼æ´æ°ãå¥å£ç¹æä»¶ä½¿ç¨ç¯å¢åéï¼è¿äºåéç±å½ä»¤è¡ä½¿ç¨ ``--env-file`` è®¾ç½®ï¼ä»¥ä¾¿ææä¿¡æ¯ä¸ä¼çå¨å½ä»¤è¡ä¸ã è§æ ¼ åæ­¢ææ°æå»ºçè¿è¡å®¹å¨ï¼ ç®å½ ä»¥ä¸é¢å¶ docker éåå¯ç¨ï¼ ä¸é¢å±ç¤ºäºå¦ä½èªå·±æå»º docker éåã ç¶åæç§ :doc:`installation` ä¸­çè¯´æå®è£ fdiï¼ä¾å¦ è¦æå»º ``httppool`` æ åï¼è¯·ä¿®æ¹ ``fdi/pns/resources/httppool_server_2.docker`` ä¸­ç ``FROM`` è¡ä»¥å é¤ ``mhastro/``ã å¨ ``httppool`` docker æ´æ°ä¸­è§å¯ ``/var/log/apache2/error-ps.log`` ï¼å¯å¨åï¼ï¼ 