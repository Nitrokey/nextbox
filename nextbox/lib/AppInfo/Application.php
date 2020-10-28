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
					$csp->addAllowedConnectDomain('127.0.0.1:18585');
					$csp->addAllowedConnectDomain('192.168.10.129:18585');
					$e->addPolicy($csp);
				
				});
    }
}

?>
