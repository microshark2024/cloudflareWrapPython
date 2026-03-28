"""Entry point for the Cloudflare WARP desktop application."""

from cloudflare_warp.app import App


def main():
    App().run()


if __name__ == "__main__":
    main()
