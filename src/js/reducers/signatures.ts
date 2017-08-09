const DEFAULT_STATE = {
    status: Sign.DownloadStatus.NotStarted
};

export default function signatures(state: Sign.Signatures = DEFAULT_STATE, action: any) {
    switch (action.type) {
        case Sign.Actions.Types.REQUEST_SIGNATURES:
            return requestSignatures(state, action);

        case Sign.Actions.Types.SET_SIGNATURE_IDS:
            return setSignatureIds(state, action);
        case Sign.Actions.Types.DELETE_SIGNATURE:
            return deleteSignature(state, action);
        default:
            return state;
    }
}

function requestSignatures(state: Sign.Signatures, action: Sign.Actions.RequestSignatures): Sign.Signatures {
    return {
        ...state,
        status: Sign.DownloadStatus.InProgress
    };
}

function setSignatureIds(state: Sign.Signatures, action: Sign.Actions.SetSignatureIds): Sign.Signatures {
    return {
        ...state,
        status: Sign.DownloadStatus.Complete,
        signatureIds: action.payload.signatureIds,
        initialIds: action.payload.initialIds
    };



function deleteSignature(state: Sign.Signatures, action: Sign.Actions.DeleteSignature): Sign.Signatures {
    return {
        ...state,
        signatureIds: state.signatureIds.filter(id => id !== action.payload.signatureId),
        initialIds: state.initialIds.filter(id => id !== action.payload.signatureId)
    };