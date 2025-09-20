import spotifyLogo from "../assets/spotify_logo_black.png";

type MainProps = {
  loggedIn: boolean;
  handleSpotifyLogin: () => void;
};

export default function Main({ loggedIn, handleSpotifyLogin }: MainProps) {
  return (
    <main className="flex-1 flex flex-col items-center justify-center p-6">
      <div className="max-w-md w-full bg-zinc-900 rounded-2xl shadow-lg p-8 text-center">
        {loggedIn ? (
          <>
            <h1 className="text-3xl font-bold mb-4">Welcome to Recapify!</h1>
            <p className="text-zinc-400 mb-6">
              You are now logged in with Spotify.
              <br />
              Weekly reports will be sent to your inbox.
            </p>
          </>
        ) : (
          <>
            <h1 className="text-3xl font-bold mb-4">Recapify</h1>
            <p className="text-zinc-400 mb-6">
              Connect your Spotify account and get weekly insights to your
              inbox!
            </p>
            <button
              onClick={handleSpotifyLogin}
              className="w-full flex items-center justify-center gap-2 text-black bg-green-600 hover:bg-green-700 py-3 px-4 rounded-lg font-semibold transition"
            >
              <img src={spotifyLogo} alt="Spotify" className="w-6 h-6" />
              Connect with Spotify
            </button>
          </>
        )}
      </div>
    </main>
  );
}
