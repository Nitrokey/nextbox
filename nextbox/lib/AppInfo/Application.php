<?php

#declare(strict_types=1);

namespace OCA\Nextbox\AppInfo;

use OC\Server;
use OCP\AppFramework\App;
use OCP\AppFramework\IAppContainer;
use OCP\IContainer;
use OCP\EventDispatcher\IEventDispatcher;
use OCP\Security\CSP\AddContentSecurityPolicyEvent;
use OCP\AppFramework\Http\ContentSecurityPolicy;

/**
 * class Application
 * 
 * @package OCA\Nextbox\AppInfo
 */
class Application extends App {
    public function __construct(array $urlParams = array()) {
        parent::__construct('nextbox', $urlParams);

				$container = $this->getContainer();
				$dispatcher = \OC::$server->getEventDispatcher();
				$dispatcher->addListener(AddContentSecurityPolicyEvent::class, function (AddContentSecurityPolicyEvent $e) {

					$csp = new ContentSecurityPolicy();
					// allow to connect to localhost
					$csp->addAllowedConnectDomain('127.0.0.1:18585');
					// allow to connect to localhost via ethernet ip
					$local_ip = getHostByName(getHostName()) + ':18585';
					$csp->addAllowedConnectDomain($local_ip);
					$e->addPolicy($csp);
				
				});
    }
}

?>
