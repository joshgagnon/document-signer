import { combineReducers, Reducer } from 'redux';
import { routerReducer as routing } from 'react-router-redux';
import { reducer as form } from 'redux-form'
import pdfStore from './pdfStore';
import documents from './documents';
import documentSets from './documentSets';
import documentSetsStatus from './documentSetsStatus';
import documentViewer from './documentViewer';
import signatures from './signatures';
import modals from './modals';
import dimensions from './dimensions';
import requestedSignatures from './requestedSignatures';
import uploadDocuments from './uploadDocuments';


const rootReducer: Reducer<Sign.State> = combineReducers<Sign.State>({
    routing,
    documentSets,
    documentSetsStatus,
    documents,
    pdfStore,
    modals,
    documentViewer,
    signatures,
    dimensions,
    requestedSignatures,
    form,
    uploadDocuments
});

export default rootReducer;
