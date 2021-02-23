<?php
namespace OCA\Nextbox\Controller;

use OCP\IRequest;
use OCP\AppFramework\Http\TemplateResponse;
use OCP\AppFramework\Http\DataResponse;
use OCP\AppFramework\Controller;
use OCP\AppFramework\Http\JSONResponse;

class PageController extends Controller {
	private $userId;
	private $backendHost;

	public function __construct($AppName, IRequest $request, $UserId){
		parent::__construct($AppName, $request);
		$this->userId = $UserId;
		$this->backendHost = "172.18.238.1:18585";
	}

	/**
	 * NoAdminRequired (deactivated, thus need admin)
	 * @NoCSRFRequired
	 */
	public function index() {
		return new TemplateResponse('nextbox', 'index');  // templates/index.php
	}
	/**
	 * @NoCSRFRequired
	 */
	public function getip($path) {
		return new JSONResponse(
			array('ip' => getHostByName(getHostName()) . ':18585')
		);
	}

	public function forward($path) {
		return new JSONResponse(
			json_decode(file_get_contents("http://" . $this->backendHost . "/" . $path))
		);
	}


	public function post($path) {
		$data = array();
		foreach($_POST as $key => $value) {
				$data[$key] = $value;
		}
		$options = array(
			'http' => array(
				'header'  => "Content-type: application/x-www-form-urlencoded\r\n",
				'method'  => 'POST',
				'content' => http_build_query($data)
			)
		);
		$context  = stream_context_create($options);
		$result = file_get_contents("http://" . $this->backendHost . "/" . $path, false, $context);
		return new JSONResponse(json_decode($result));
	}
}
