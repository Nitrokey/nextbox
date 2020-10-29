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

	public function token() {
		$token = md5(rand() + uniqid());

		// @todo: maybe reuse sessios-saved or cookie-saved token instead of creating a new one

		$out = file_get_contents("http://127.0.0.1:18585/token/" . $token . 
			"/" . $this->request->getRemoteAddress());

		return new JSONResponse(array('token' => $token));
	}

}
