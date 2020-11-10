<?php
namespace OCA\Nextbox\Controller;

use OCP\IRequest;
use OCP\AppFramework\Http\TemplateResponse;
use OCP\AppFramework\Http\DataResponse;
use OCP\AppFramework\Controller;
use OCP\AppFramework\Http\JSONResponse;

class PageController extends Controller {
	private $userId;

	public function __construct($AppName, IRequest $request, $UserId){
		parent::__construct($AppName, $request);
		$this->userId = $UserId;
	}

	/**
	 * NoAdminRequired (deactivated, thus need admin)
	 * @NoCSRFRequired
	 */
	public function index() {
		return new TemplateResponse('nextbox', 'index');  // templates/index.php
	}

	/*public function token() {
		$token = md5(rand() + uniqid());

		// @todo: maybe reuse sessios-saved or cookie-saved token instead of creating a new one

		$out = file_get_contents("http://127.0.0.1:18585/token/" . $token . 
			"/" . $this->request->getRemoteAddress());

		return new JSONResponse(array('token' => $token));
	}*/

	public function forward($path) {
		return new JSONResponse(
			json_decode(file_get_contents("http://127.0.0.1:18585/" . $path))
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
		$result = file_get_contents("http://127.0.0.1:18585/" . $path, false, $context);
		return new JSONResponse(json_decode($result));

			#http_post_data("http://127.0.0.1:18585/" . $path, $_POST)
			#json_decode();
		#);
	}
}
