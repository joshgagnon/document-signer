import { all, takeEvery, put, call, select } from 'redux-saga/effects';
import axios from 'axios';
import { setSignRequestStatus, showResults, closeModal, showFailureModal, setSaveStatus } from '../actions';
import { push } from 'react-router-redux';
import { findSetForDocument, stringToCanvas } from '../utils';

function *signDocumentWithRedirect(action: Sign.Actions.SignDocument){
    const success = yield signDocument(action);
    if(success){
        yield put(push(`/documents/${action.payload.documentSetId}`));
    }
}

function *signDocument(action: Sign.Actions.SignDocument) {
    const status = yield select((state: Sign.State) => state.documentViewer.signRequestStatus);
    if(status === Sign.DownloadStatus.InProgress){
        return;
    }
    yield put(setSignRequestStatus(Sign.DownloadStatus.InProgress));

    const documentViewer = yield select((state: Sign.State) => state.documentViewer);

    const signatures = Object.keys(documentViewer.signatures).map(key => documentViewer.signatures[key]).filter(signature => signature.documentId === action.payload.documentId);
    const dates = Object.keys(documentViewer.dates).map(key => documentViewer.dates[key]).filter(date => date.documentId === action.payload.documentId);
    const texts = Object.keys(documentViewer.texts).map(key => documentViewer.texts[key]).filter(text => text.documentId === action.payload.documentId);

    const overlays = [...dates, ...texts].map(o => {
        const canvas = stringToCanvas(o.height * 4, o.value);
        const dataUrl = canvas.toDataURL();
        return {...o, dataUrl}
    });

    const postPayload = {
        ...action.payload,
        signatures,
        overlays
    };

    try {
        const response = yield call(axios.post, '/api/sign', postPayload);

        yield all([
            put(setSignRequestStatus(Sign.DownloadStatus.Complete)),
            put(closeModal({ modalName: Sign.ModalType.SIGN_CONFIRMATION })),
        ]);
        return true;
    }
    catch (e) {
        yield all([
            put(closeModal({ modalName: Sign.ModalType.SIGN_CONFIRMATION })),
            put(setSignRequestStatus(Sign.DownloadStatus.Failed))
        ]);
    }
}


function hasSomethingToSign(documentViewer : Sign.DocumentViewer, documentId : string) {
    const signatures = Object.keys(documentViewer.signatures).map(key => documentViewer.signatures[key]).filter(signature => signature.documentId === documentId);
    const dates = Object.keys(documentViewer.dates).map(key => documentViewer.dates[key]).filter(date => date.documentId === documentId);
    const texts = Object.keys(documentViewer.texts).map(key => documentViewer.texts[key]).filter(text => text.documentId === documentId);
    return signatures.length || dates.length || texts.length;
}

function *submitDocumentSet() {
    yield takeEvery(Sign.Actions.Types.SUBMIT_SIGN_REQUESTS, submit);

    function *submit(action: Sign.Actions.SubmitSignRequests) {
        const documentViewer = yield select((state: Sign.State) => state.documentViewer);
        const documentSets = yield select((state: Sign.State) => state.documentSets);
        const documentIds = documentSets[action.payload.documentSetId].documentIds;

        for(let documentId of documentIds){
            if(hasSomethingToSign(documentViewer, documentId)){
                yield signDocument({type: Sign.Actions.Types.SIGN_DOCUMENT, payload: {documentSetId: action.payload.documentSetId, documentId}} as Sign.Actions.SignDocument);
            }
        }
        const status = yield select((state: Sign.State) => state.documentViewer.signRequestStatus);
        if(status === Sign.DownloadStatus.InProgress){
            return;
        }
        try {
            if(action.payload.signatureRequests.length){
                yield put(setSignRequestStatus(Sign.DownloadStatus.InProgress));
                const response = yield call(axios.post, '/api/request_signatures', action.payload);
            }

            yield all([
                put(setSignRequestStatus(Sign.DownloadStatus.Complete)),
                put(closeModal({ modalName: Sign.ModalType.SUBMIT_CONFIRMATION })),
                put(push(`/documents/${action.payload.documentSetId}`)),
            ]);
        }
        catch (e) {
            yield all([
                put(closeModal({ modalName: Sign.ModalType.SUBMIT_CONFIRMATION })),
                put(showFailureModal({message: 'Sorry, we could not send invitations at this time.'})),
                put(setSignRequestStatus(Sign.DownloadStatus.Failed))
            ]);
        }
    }
}

function *saveDocumentViewSaga() {
    yield takeEvery(Sign.Actions.Types.SAVE_DOCUMENT_VIEW, saveDocumentView);

    function *saveDocumentView(action: Sign.Actions.SaveDocumentView) {
        const recipients = yield select((state: Sign.State) => state.documentSets[action.payload.documentSetId].recipients);
        const documentView = yield select((state: Sign.State) => state.documentViewer);
        const remove = (obj: any) => {
            Object.keys(obj).map(k => {
                if(obj[k].documentId !== action.payload.documentId){
                    delete obj[k];
                }
            })
            return obj;
        }
        const signatures = remove({...documentView.signatures});
        const prompts = remove({...documentView.prompts})
        const texts = remove({...documentView.texts})
        const dates = remove({...documentView.dates})
        yield put(setSaveStatus({status: Sign.DownloadStatus.InProgress, documentId: action.payload.documentId}));
        const view = {
            signatures, prompts, texts, dates
        }
        try{
            const response = yield call(axios.post, `/api/save_view/${action.payload.documentId}`, {recipients, view});
            yield put(setSaveStatus({status: Sign.DownloadStatus.Complete, documentId: action.payload.documentId}));
        }
        catch(e) {
            yield put(setSaveStatus({status: Sign.DownloadStatus.Failed, documentId: action.payload.documentId}));
        }

    }
}

export default [submitDocumentSet(), saveDocumentViewSaga()];