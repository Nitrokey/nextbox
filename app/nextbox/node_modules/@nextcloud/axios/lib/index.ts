import Axios, { AxiosInstance, CancelTokenStatic } from 'axios'
import { getRequestToken, onRequestTokenUpdate } from '@nextcloud/auth'

interface CancelableAxiosInstance extends AxiosInstance {
	CancelToken: CancelTokenStatic
	isCancel(value: any): boolean
}

const client: any = Axios.create({
	headers: {
		requesttoken: getRequestToken() ?? ''
	}
})
const cancelableClient: CancelableAxiosInstance = Object.assign(client, {
	CancelToken: Axios.CancelToken,
	isCancel: Axios.isCancel,
})

onRequestTokenUpdate(token => client.defaults.headers.requesttoken = token)

export default cancelableClient
