import { AxiosInstance, CancelTokenStatic } from 'axios';
interface CancelableAxiosInstance extends AxiosInstance {
    CancelToken: CancelTokenStatic;
    isCancel(value: any): boolean;
}
declare const cancelableClient: CancelableAxiosInstance;
export default cancelableClient;
