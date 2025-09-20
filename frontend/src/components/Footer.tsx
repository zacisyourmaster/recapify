export default function Footer() {
  return (
    <footer className="w-full bg-zinc-900 text-zinc-400 py-4 mt-auto text-center border-t border-zinc-800">
      <div className="max-w-md mx-auto">
        <p className="mb-2">
          <strong>Recapify</strong> is a personal Spotify recap app. Sign up
          with your Spotify account and get weekly listening insights delivered
          to your inbox. Stay on top of your music habits and discover your top
          tracks and artists every week!
        </p>
        <p>
          Webpage by{" "}
          <a href="https://zacisyourmaster.github.io" className="underline">
            Zach Smith
          </a>
        </p>
      </div>
    </footer>
  );
}
