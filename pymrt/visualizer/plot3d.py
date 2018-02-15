import sys
import numpy as np
from mayavi import mlab
from mayavi.scripts import mayavi2
from traits.api import HasTraits, Button, Instance
from traitsui.api import View, Item


def plot3d_sensor_vector(dataset, embeddings):
    """Plot sensor embedding in 3D space using mayavi.

    Given the dataset and a sensor embedding matrix, each sensor is shown as
    a sphere in the 3D space. Note that the shape of embedding matrix is
    (num_sensors, 3) where num_sensors corresponds to the length of
    ``dataset.sensor_list``.

    Args:
        dataset (:obj:`~pymrt.casas.CASASDataset`): CASAS smart home dataset.
        embeddings (:obj:`numpy.ndarray`): 3D sensor vector embedding.
    """
    figure = mlab.figure('Sensor Embedding (3D)')
    figure.scene.disable_render = True
    points = mlab.points3d(embeddings[:, 0], embeddings[:, 1], embeddings[:, 2],
                           scale_factor=0.03)
    for i, x in enumerate(embeddings):
        mlab.text3d(x[0], x[1], x[2], dataset.sensor_list[i]['name'],
                    scale=(0.02, 0.02, 0.02))
    mlab.outline(None, color=(.7, .7, .7), extent=[-1, 1, -1, 1, -1, 1])
    ax = mlab.axes(None, color=(.7, .7, .7), extent=[-1, 1, -1, 1, -1, 1],
                   ranges=[-1, 1, -1, 1, -1, 1], nb_labels=6)
    ax.label_text_property.font_size = 3
    ax.axes.font_factor = 0.4
    figure.scene.disable_render = False
    mlab.show()


def plot3d_sensor_with_gm(dataset, embeddings, grid, gm_s=None, gm_list=None,
                          observation=None, title=None, contours=4,
                          log_plot=True):
    """3D plot of CASAS sensor embedding with GM-PHD sampled by grid.

    Multi-target PHD represented either by scalar ``gm_s`` or Gaussian Mixture
    ``gm_list`` is plotted as 3D contour graph with mayavi.
    Current observations and sensor embedding are plotted as spheres as well.

    Args:
        dataset (:obj:`~pymrt.casas.CASASDataset`): CASAS smart home dataset.
        embeddings (:obj:`numpy.ndarray`): 3D sensor vector embedding of shape
            (num_sensors, 3) where num_sensors corresponds to the length of
            ``dataset.sensor_list``.
        grid (:obj:`numpy.ndarray`): 3D mesh generated by :func:`numpy.mgrid` or
            :func:`numpy.meshgrid`.
        gm_s (:obj:`numpy.ndarray`): Multi-target PHD scalar sampled at each
            point defined by the 3D mesh grid ``grid``.
        gm_list (:obj:`list`): List of
            :obj:`~pymrt.tracking.utils.GaussianComponent` representing the
            multi-target PHD at the moment. If ``gm_s`` is None, this list is
            used to generate the PHD scalar for plotting.
        observation (:obj:`list`): List of observations to be plotted. Each
            observation is a :obj:`numpy.ndarray` of shape (n, 1). It has to
            be the embedding vector of one of the sensor in the dataset.
        title (:obj:`string`): Plot title.
        contours (:obj:`int`): Number of contour surfaces to draw.
        log_plot (:obj:`bool`): Plot ``gm_s`` in log scale.
    """
    if gm_s is None:
        if gm_list is None:
            raise ValueError("Must provide 3D sampled GM scalar gm_s or a "
                             "Gaussian Mixture list")
        else:
            print('Sampling PHD in 3D space')
            from ..tracking.utils import gm_calculate
            gm_s = gm_calculate(gm_list=gm_list, grid=grid)
    if title is None:
        title = 'PHD'

    print('Start Plotting with Mayavi')
    figure = mlab.figure(dataset.get_name() + ' ' + title)
    figure.scene.disable_render = True
    if log_plot:
        contour_s = np.log(gm_s + np.finfo(np.float).tiny)
    else:
        contour_s = gm_s
    # Plot Contour Surf first
    contour = mlab.contour3d(
        grid[0],
        grid[1],
        grid[2],
        contour_s,
        contours=contours,
        transparent=True,
        opacity=0.5
    )

    mlab.colorbar(contour, title='PHD', orientation='vertical')

    points = mlab.points3d(embeddings[:, 0], embeddings[:, 1], embeddings[:, 2],
                           scale_factor=0.03)

    if observation is not None:
        obs_array = np.block(observation).T
        obs_points = mlab.points3d(
            obs_array[:, 0], obs_array[:, 1], obs_array[:, 2],
            scale_factor=0.03, color=(0, 0, 1)
        )

    for i, x in enumerate(embeddings):
        mlab.text3d(x[0], x[1], x[2], dataset.sensor_list[i]['name'],
                    scale=(0.02, 0.02, 0.02))
    mlab.outline(None, color=(.7, .7, .7), extent=[-1, 1, -1, 1, -1, 1])
    ax = mlab.axes(None, color=(.7, .7, .7), extent=[-1, 1, -1, 1, -1, 1],
                   ranges=[-1, 1, -1, 1, -1, 1], nb_labels=6)
    ax.label_text_property.font_size = 3
    ax.axes.font_factor = 0.4
    figure.scene.disable_render = False
    mlab.show()


def animate_sensor_with_gm(dataset, embeddings, grid, gm_s_list=None,
                           gm_list_list=None, observation_list=None,
                           title=None, contours=4, log_plot=True):
    """ 3D plot of CASAS sensor embedding with GM-PHD sampled by grid.

    Multi-target PHD represented either by scalar ``gm_s`` or Gaussian Mixture
    ``gm_list`` is plotted as 3D contour graph with mayavi.
    Current observations and sensor embedding are plotted as spheres as well.
    It wraps the whole sequence in a mayavi application, user can go back and
    forth in time and visually see how the PHD changes in time.

    Args:
        dataset (:obj:`~pymrt.casas.CASASDataset`): CASAS smart home dataset.
        embeddings (:obj:`numpy.ndarray`): 3D sensor vector embedding of shape
            (num_sensors, 3) where num_sensors corresponds to the length of
            ``dataset.sensor_list``.
        grid (:obj:`numpy.ndarray`): 3D mesh generated by :func:`numpy.mgrid` or
            :func:`numpy.meshgrid`.
        gm_s_list (:obj:`list`): List of PHD scalars at each time step.
        gm_list_list (:obj:`list`): List of Gaussian Mixtures at each time step.
            If ``gm_s_list`` is None, it is used along with ``grid`` to generate
            the PHD scalar at each time step.
        observation_list (:obj:`list`): List of observations at each time step.
        title (:obj:`string`): Plot title.
        contours (:obj:`int`): Number of contour surfaces to draw.
        log_plot (:obj:`bool`): Plot ``gm_s`` in log scale.
    """
    if gm_s_list is None:
        if gm_list_list is None:
            raise ValueError("Must provide 3D sampled GM scalar gm_s or a "
                             "Gaussian Mixture list")
        else:
            print('Sampling PHD in 3D space')
            from ..tracking.utils import gm_calculate
            gm_s_list = []
            i = 0
            for gm_list in gm_list_list:
                sys.stdout.write('calculate gm_scalar for step %d' % i)
                gm_s_list.append(gm_calculate(
                    gm_list=gm_list, grid=grid
                ))
                i += 1
    if title is None:
        title = 'PHD'

    print('Start Plotting with Mayavi')

    class Controller(HasTraits):
        next_frame = Button('Next Frame')
        previous_frame = Button('Previous Frame')
        view = View(
            Item(name='next_frame'),
            Item(name='previous_frame')
        )
        current_frame = 0

        play_state = False

        def _next_frame_changed(self, value):
            """Goto next frame"""
            if self.current_frame + 1 < len(gm_s_list):
                self.current_frame += 1
                self.update_frame()

        def _previous_frame_changed(self, value):
            """Goto previous frame"""
            if self.current_frame - 1 >= 0:
                self.current_frame -= 1
                self.update_frame()

        def update_frame(self):
            print('Frame %d' % self.current_frame)
            if log_plot:
                contour_s = np.log(
                    gm_s_list[self.current_frame] + np.finfo(np.float).tiny
                )
            else:
                contour_s = gm_s_list[self.current_frame]
            self.phd_contour.mlab_source.set(
                scalars=contour_s
            )
            self.color_vector[:] = 0.
            if observation_list is not None:
                obs_array = observation_list[self.current_frame]
                obs_index = [
                    np.where(
                        np.all(embeddings == sensor_vec.flatten(), axis=1)
                    )[0][0]
                    for sensor_vec in obs_array
                ]
                self.color_vector[obs_index] = 1.
                self.sensor_points.mlab_source.dataset.point_data.scalars = \
                    self.color_vector
            mlab.draw()

    @mayavi2.standalone
    def main_view():
        """Example showing how to view a 3D numpy array in mayavi2.
        """
        figure = mlab.figure(dataset.get_name() + ' ' + title)

        if log_plot:
            contour_s = np.log(gm_s_list[0] + np.finfo(np.float).tiny)
        else:
            contour_s = gm_s_list[0]

        # Plot Contour Surf first
        contour = mlab.contour3d(
            grid[0],
            grid[1],
            grid[2],
            contour_s,
            contours=contours,
            transparent=True,
            opacity=0.5
        )

        mlab.colorbar(contour, title='PHD', orientation='vertical')

        points = mlab.points3d(
            embeddings[:, 0], embeddings[:, 1], embeddings[:, 2],
            scale_factor=0.03
        )

        points.glyph.scale_mode = 'scale_by_vector'
        points.mlab_source.dataset.point_data.vectors = np.tile(
            np.ones(embeddings.shape[0]), (3, 1))
        color_vector = np.zeros(embeddings.shape[0])
        points.mlab_source.dataset.point_data.scalars = color_vector

        if observation_list is not None:
            obs_array = observation_list[0]
            obs_index = [
                np.where(
                    np.all(embeddings == sensor_vec.flatten(), axis=1)
                )[0][0]
                for sensor_vec in obs_array
            ]
            color_vector[obs_index] = 1.

        for i, x in enumerate(embeddings):
            mlab.text3d(x[0], x[1], x[2], dataset.sensor_list[i]['name'],
                        scale=(0.02, 0.02, 0.02))
        mlab.outline(None, color=(.7, .7, .7), extent=[0, 1, 0, 1, 0, 1])
        ax = mlab.axes(None, color=(.7, .7, .7), extent=[0, 1, 0, 1, 0, 1],
                       ranges=[0, 1, 0, 1, 0, 1], nb_labels=6)
        ax.label_text_property.font_size = 3
        ax.axes.font_factor = 0.4
        computation = Controller(
            sensor_points=points,
            phd_contour=contour,
            color_vector=color_vector,
            figure=figure
        )
        computation.edit_traits()

    main_view()
