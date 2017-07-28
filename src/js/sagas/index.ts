import { select, takeEvery, put, call } from 'redux-saga/effects';
import { SagaMiddleware, delay } from 'redux-saga';
import axios from 'axios';
import { updateDocument } from '../actions';

import pdfStoreSagas from './pdfStoreSagas';

export default function *rootSaga(): any {
    yield [
        readDocumentSaga(),
        ...pdfStoreSagas
    ];
}

function *readDocumentSaga() {
    yield takeEvery(Sign.Actions.Types.ADD_DOCUMENT, readDocument);

    function *readDocument(action: Sign.Actions.AddDocument) {
        // Update file upload progress
        yield put(updateDocument({ id: action.payload.id, readStatus: Sign.DocumentReadStatus.InProgress }));

        // Create file reader, read file to BLOB, then call the updateDocument action
        const fileReader = new FileReader();
        fileReader.readAsArrayBuffer(action.payload.file);
        fileReader.onload = function*() {
            yield put(updateDocument({
                id: action.payload.id,
                data: fileReader.result,
                readStatus: Sign.DocumentReadStatus.Complete
            }));
        }
    }
}