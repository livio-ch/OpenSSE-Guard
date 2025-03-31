import { useAuth0 } from "@auth0/auth0-react";

export const useAuth = () => {
  const { getAccessTokenSilently, isAuthenticated } = useAuth0();

  const fetchToken = async () => {
    if (isAuthenticated) {
      return await getAccessTokenSilently();
    }
    return null;
  };

  return { fetchToken, isAuthenticated };
};
