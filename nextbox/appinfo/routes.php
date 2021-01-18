<?php
/**
 * Create your routes in here. The name is the lowercase name of the controller
 * without the controller part, the stuff after the hash is the method.
 * e.g. page#index -> OCA\Nextbox\Controller\PageController->index()
 *
 * The controller class has to be registered in the application.php file since
 * it's instantiated in there
 */
return [
    'routes' => [
			['name' => 'page#index', 'url' => '/', 'verb' => 'GET'],
			['name' => 'page#getip', 'url' => '/getip', 'verb' => 'GET'],
			['name' => 'page#forward', 'url' => '/forward/{path}', 'verb' => 'GET', 
			 'requirements' => array('path' => '.+')],
			['name' => 'page#post', 'url' => '/forward/{path}', 'verb' => 'POST', 
			 'requirements' => array('path' => '.+')],

    ]
];
