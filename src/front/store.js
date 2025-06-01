export const initialStore=()=>{
  return{
    user: null,
  }
}

export default function storeReducer(store, action = {}) {
  switch(action.type){
    case "login":
      return {
        ...store,
        user: action.payload.user,
      };
    case "logout":
      return {
        ...store,
        user: null,
      };
    default:
      throw Error('Unknown action.');
  }    
}
